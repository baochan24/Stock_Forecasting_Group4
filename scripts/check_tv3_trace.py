"""Accept TV2 input and verify trace before/after synthetic update and reload."""
from datetime import datetime,timezone
import argparse
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.artifacts.scaler import load_scaler
from backend.artifacts.prepared import load_prepared_modes
from backend.data.preparation.tensors import make_lstm_inputs
from backend.data.preparation.contracts import validate_forecast_input
from backend.data.validation.validator import compute_sha256
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.model_trace import trace_lstm


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-version',required=True)
    parser.add_argument('--scaler-dir',required=True)
    parser.add_argument('--prepared-dir',required=True)
    args=parser.parse_args()
    torch.set_num_threads(1)
    snapshot=load_tv1_snapshot(ROOT,args.dataset_version)
    protected=[Path(p) for p in snapshot['paths'].values()]+[Path(args.scaler_dir)/n for n in ['scaler.json','manifest.json']]
    protected += [p for p in Path(args.prepared_dir).iterdir() if p.is_file()]
    hashes={str(p):compute_sha256(p) for p in protected}
    folder=ROOT/'logs/audit'/('tv3_trace_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True,exist_ok=False)
    rows,artifacts=[],{}
    with patch.object(StandardScaler,'fit',side_effect=AssertionError('no fit')),patch.object(StandardScaler,'partial_fit',side_effect=AssertionError('no fit')):
        scaler,scaler_manifest=load_scaler(args.scaler_dir,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot['acceptance']['hashes'])
        modes,prepared_manifest=load_prepared_modes(args.prepared_dir,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot['acceptance']['hashes'],expected_scaler_id=scaler_manifest['scaler_id'])
        for h,cls in [(1,LSTMOneStep),(5,LSTMMultiStep)]:
            record=modes[h]['splits']['train']['inputs'][0]
            validate_forecast_input(record)
            i=int(modes[h]['splits']['train']['target_indices'][0])
            if record['input_dates'] != snapshot['data'].date.iloc[i-30:i].tolist(): raise AssertionError('Input session mismatch')
            np.testing.assert_array_equal(record['input_values'].ravel(),snapshot['data'].adjusted_close.iloc[i-30:i].to_numpy())
            x=make_lstm_inputs([record],scaler,dataset_version=args.dataset_version,forecast_length=h)['X']
            torch.manual_seed(42)
            model=cls().cpu().eval()
            initial=trace_lstm(model,x)
            # Only a synthetic optimizer probe, not training on AAPL targets.
            model.train()
            optimizer=torch.optim.Adam(model.parameters(),lr=.001)
            optimizer.zero_grad()
            synthetic_x=torch.linspace(-1,1,30,dtype=torch.float64).reshape(1,30,1)
            model(synthetic_x).square().mean().backward(); optimizer.step(); model.eval()
            weights={k:v.clone() for k,v in model.state_dict().items()}
            grads=[p.grad.clone() if p.grad is not None else None for p in model.parameters()]
            x_before=x.clone()
            updated=trace_lstm(model,x)
            if initial['prediction_scaled']==updated['prediction_scaled']: raise AssertionError('Probe did not alter weights/output')
            buffer=io.BytesIO(); torch.save(model.state_dict(),buffer); buffer.seek(0)
            restored=cls().cpu().eval()
            restored.load_state_dict(torch.load(buffer,map_location='cpu',weights_only=True),strict=True)
            reloaded=trace_lstm(restored,x)
            if reloaded != updated: raise AssertionError('Reloaded trace changed')
            for key,value in model.state_dict().items(): torch.testing.assert_close(value,weights[key],rtol=0,atol=0)
            for parameter,before in zip(model.parameters(),grads): torch.testing.assert_close(parameter.grad,before,rtol=0,atol=0)
            torch.testing.assert_close(x,x_before,rtol=0,atol=0)
            if model.training or model.lstm.training or model.fc.training: raise AssertionError('Mode changed')
            for stage,trace in [('initial',initial),('after_synthetic_step',updated),('after_reload',reloaded)]:
                name=f'f{h}_{stage}.json'
                envelope={'dataset_version':args.dataset_version,'sample_id':record['sample_id'],'forecast_origin':record['forecast_origin'],
                          'input_dates':record['input_dates'],'forecast_length':h,'stage':stage,
                          'scope':'Diagnostic only; random weights or one synthetic Adam step, no trained forecasting checkpoint.', 'trace':trace}
                text=json.dumps(envelope,allow_nan=False,indent=2)
                if json.loads(text)['trace'] != trace: raise AssertionError('JSON changed trace')
                (folder/name).write_text(text,encoding='utf-8')
                artifacts[name]=compute_sha256(folder/name)
                rows.append({'forecast_length':h,'stage':stage,**trace['verification']})
    if hashes != {str(p):compute_sha256(p) for p in protected}: raise AssertionError('Source artifacts changed')
    summary={'passed':True,'dataset_version':args.dataset_version,'scaler_id':scaler_manifest['scaler_id'],'prepared_id':prepared_manifest['prepared_id'],
             'checks':rows,'trace_files':artifacts,'protected_hashes':hashes,'dtype':'float64','reload_trace_exact':True,
             'weights_gradients_input_mode_unchanged_by_trace':True,'source_hashes':{'backend/model_trace/lstm_trace.py':compute_sha256(ROOT/'backend/model_trace/lstm_trace.py')},
             'python':sys.version,'executable':sys.executable,'torch':torch.__version__,
             'scope':'Two representative train inputs, 3 stages per model, not stock prediction accuracy or official checkpoint training.'}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'checks':rows,'evidence':str(folder/'summary.json')},indent=2))


if __name__=='__main__': main()
