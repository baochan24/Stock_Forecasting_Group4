"""TV6 item6: existing test errors plus validation-only LSTM input diagnostics."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol
from backend.artifacts.scaler import load_scaler
from backend.data.transforms.anchored_price import encode_history,decode_prices,REPRESENTATION
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.error_analysis.lstm_diagnostics import history_controls,describe,summarize_errors


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')


def main():
    protocol=read(ROOT/PROTOCOL_PATH);protocol_sha=validate_protocol(protocol,ROOT)
    test_folder=(ROOT/read(ROOT/'logs/audit/tv6_item5_latest.json')['evidence']).parent
    dev_folder=(ROOT/read(ROOT/'logs/audit/tv6_residual_development_latest.json')['evidence']).parent
    test=read(test_folder/'summary.json');dev=read(dev_folder/'summary.json')
    if not test['passed'] or not dev['passed'] or dev['runs_completed']!=36:raise ValueError('Source acceptance')
    watch=dict(protocol['semantic']['artifacts_sha256'])
    for receipt in [test,dev]:
        for name,expected in receipt['source_hashes'].items():
            if sha(ROOT/name)!=expected:raise ValueError('Changed input '+name)
            watch[name]=expected
    for folder in (test_folder,dev_folder):
        audit=read(folder/'independent_audit.json')
        if not audit['passed']:raise ValueError('Missing independent acceptance')
        for name,expected in audit['result_hashes'].items():
            if sha(folder/name)!=expected:raise ValueError('Changed result '+name)
            watch[(folder/name).relative_to(ROOT).as_posix()]=expected
    for name in ['scripts/analyze_tv6_item6.py','backend/error_analysis/lstm_diagnostics.py','tests/evaluation/test_lstm_diagnostics.py']:
        watch[name]=sha(ROOT/name)
    folder=ROOT/'logs/audit'/('tv6_item6_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    summary=dict(passed=False,status='running',scope='post-test error analysis and validation-only history stress',
        protocol_sha256=protocol_sha,source_hashes=watch,test_source=str(test_folder.relative_to(ROOT)),dev_source=str(dev_folder.relative_to(ROOT)),
        new_test_inference=False,training_performed=False,weights_changed=False,fix_performed=False,
        controls=['real','flat','reverse_prefix','shuffle_prefix'],control_rng_seed=20261127,rolling_sessions=20,top_n=10)
    write(folder/'summary.json',summary)
    try:
        inventory=read(ROOT/'reports/audits/TV6_Input_Inventory.json');version=inventory['dataset_version']
        prices=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip').set_index('date').adjusted_close
        thresholds={}
        for end_year in (2021,2022):
            p=prices.loc[:f'{end_year}-12-31'].to_numpy()
            thresholds[end_year]={k:float(np.quantile(np.abs((p[29+k:]-p[29:-k])/p[29:-k]),.95)) for k in range(1,6)}
        write(folder/'stress_thresholds.json',thresholds)
        original=pd.read_csv(test_folder/'residuals.csv',float_precision='round_trip')
        original['origin_price']=original.forecast_origin.map(prices)
        np.testing.assert_allclose(original.actual_price,[prices[d] for d in original.target_date],rtol=0,atol=1e-12)
        original['cohort']='official_test_2024_2025';original['representation']='absolute-price-v1'
        contexts=[(original,thresholds[2022])]
        for year in (2022,2023):
            frames=[]
            for run in dev['runs']:
                if run['validation_year']!=year or run['representation']!=REPRESENTATION or not run['task'].startswith('lstm'):continue
                run_id=f'{year}_{run["task"]}_residual_seed{run["seed"]}'
                p=dev_folder/run_id/'validation_predictions.csv';watch[p.relative_to(ROOT).as_posix()]=sha(p)
                frame=pd.read_csv(p,float_precision='round_trip')
                frame['origin_price']=frame.baseline_price
                frame['method']='lstm';frame['seed']=run['seed'];frame['forecast_length']=5 if run['task']=='lstm_h5' else 1
                frame['cohort']=f'development_{year}';frame['representation']=REPRESENTATION;frames.append(frame)
            contexts.append((pd.concat(frames,ignore_index=True),thresholds[year-1]))
        outputs={}
        for frame,threshold in contexts:
            for name,table in summarize_errors(frame,threshold).items():outputs.setdefault(name,[]).append(table)
        for name,tables in outputs.items():pd.concat(tables,ignore_index=True).to_csv(folder/(name+'.csv'),index=False)
        # Sensitivity: only the 12 existing residual LSTM checkpoints on their development fold.
        torch.set_num_threads(1)
        probes=[];probe_rows=[];model_checks=[]
        for run in dev['runs']:
            if run['representation']!=REPRESENTATION or not run['task'].startswith('lstm'):continue
            year=run['validation_year'];h=5 if run['task']=='lstm_h5' else 1
            checkpoint=ROOT/run['checkpoint'];manifest=read(checkpoint/'manifest.json')
            if manifest['purpose']!='post-test-development-not-release' or manifest['representation_version']!=REPRESENTATION:
                raise ValueError('Wrong checkpoint representation/purpose')
            if manifest['seed']!=run['seed'] or manifest['validation_year']!=year or manifest['dataset_version']!=version:
                raise ValueError('Checkpoint reference mismatch')
            for path in (checkpoint/'manifest.json',checkpoint/'state_dict.pt'):
                watch[path.relative_to(ROOT).as_posix()]=sha(path)
            if sha(checkpoint/'state_dict.pt')!=manifest['checkpoint_sha256']:raise ValueError('Checkpoint hash')
            sf=ROOT/'artifacts/scalers'/manifest['scaler_id']
            for path in (sf/'manifest.json',sf/'scaler.json'):watch[path.relative_to(ROOT).as_posix()]=sha(path)
            scaler,sm=load_scaler(sf,expected_dataset_version=version,expected_source_hashes=inventory['source_hashes'])
            if sm['metadata']['fit_last_date']>=f'{year}-01-01':raise ValueError('Scaler leakage')
            cohort=next(c for c in protocol['semantic']['cohorts'] if c['forecast_length']==h)
            base=ROOT/'data/prepared'/cohort['prepared_id'];split='train' if year==2022 else 'val'
            xx=read(base/f'f{h}_{split}_inputs.json');yy=read(base/f'f{h}_{split}_targets.json')
            pairs=[(x,y) for x,y in zip(xx,yy) if all(d.startswith(str(year)) for d in y['target_dates'])]
            if not pairs or any(x['sample_id']!=y['sample_id'] for x,y in pairs):raise ValueError('Diagnostic cohort pairing')
            raw=np.array([x['input_values'] for x,y in pairs],dtype=np.float64)
            actual=np.array([y['target_values'] for x,y in pairs],dtype=np.float64)
            model=LSTMOneStep() if h==1 else LSTMMultiStep()
            model.load_state_dict(torch.load(checkpoint/'state_dict.pt',weights_only=True,map_location='cpu'));model.eval()
            for p in model.parameters():p.requires_grad_(False)
            before={k:v.clone() for k,v in model.state_dict().items()}
            saved=pd.read_csv(dev_folder/f'{year}_{run["task"]}_residual_seed{run["seed"]}'/'validation_predictions.csv',float_precision='round_trip')
            real=None
            for control,history in history_controls(raw).items():
                x,anchor=encode_history(history,scaler.scale_[0])
                with torch.inference_mode():
                    delta=torch.cat([model(torch.from_numpy(x[i:i+32])) for i in range(0,len(x),32)]).numpy()
                predicted=decode_prices(delta,anchor,scaler.scale_[0])
                if control=='real':
                    real=predicted.copy()
                    np.testing.assert_allclose(real.reshape(-1),saved.predicted_price,rtol=0,atol=1e-12)
                    if [(x['sample_id'],d) for x,y in pairs for d in y['target_dates']]!=list(zip(saved.sample_id,saved.target_date)):
                        raise ValueError('Saved diagnostic key order')
                rows=[]
                for i,(inp,target) in enumerate(pairs):
                    for k in range(h):rows.append(dict(validation_year=year,forecast_length=h,seed=run['seed'],control=control,
                        sample_id=inp['sample_id'],forecast_origin=inp['forecast_origin'],target_date=target['target_dates'][k],horizon_step=k+1,
                        origin_price=float(anchor[i]),actual_price=float(actual[i,k]),predicted_price=float(predicted[i,k]),
                        real_predicted_price=float(real[i,k])))
                part=pd.DataFrame(rows);probe_rows.extend(rows)
                for step in list(range(1,h+1))+([0] if h==5 else []):
                    g=part if step==0 else part[part.horizon_step==step]
                    probes.append(dict(validation_year=year,forecast_length=h,seed=run['seed'],control=control,
                        horizon_step=None if step==0 else step,metric_scope='overall' if step==0 else 'per_horizon',
                        mean_abs_change_from_real_usd=float((g.predicted_price-g.real_predicted_price).abs().mean()),**describe(g)))
            for key,value in model.state_dict().items():
                if not torch.equal(before[key],value):raise ValueError('Model mutated')
            if any(p.grad is not None or p.requires_grad for p in model.parameters()):raise ValueError('Grad enabled')
            model_checks.append(dict(validation_year=year,forecast_length=h,seed=run['seed'],real_matches_saved=True,
                controls=4,parameters_unchanged=True))
        pd.DataFrame(probes).to_csv(folder/'history_probes.csv',index=False)
        pd.DataFrame(probe_rows).to_csv(folder/'history_probe_predictions.csv',index=False)
        # Probe comparisons are descriptive, all seeds retained.
        if len(model_checks)!=12:raise ValueError('Missing LSTM seeds/modes/folds')
        for name,expected in watch.items():
            if sha(ROOT/name)!=expected:raise ValueError('Source changed '+name)
        validate_protocol(protocol,ROOT)
        summary.update(status='completed',passed=True,source_hashes=watch,models_probed=12,model_checks=model_checks,
            probe_rows=len(probe_rows),source_artifacts_unchanged=True,limitations=[
                'Synthetic history controls can be out of distribution; sensitivity is not causal predictive value',
                'Validation used for checkpoint selection; no independent performance claim',
                'Stress labels use actual changes after the fact, not deployable forecasting inputs',
                'Overlapping horizons and months are dependent; no significance claims'])
        write(folder/'summary.json',summary)
        write(ROOT/'logs/audit/tv6_item6_latest.json',dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()))
        print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),models_probed=12,probe_rows=len(probe_rows))))
        print(pd.DataFrame(probes).query('forecast_length==1').groupby(['validation_year','control'])[
            ['mae_usd','rmse_usd','mean_abs_change_from_real_usd','std_adjustment_usd']].mean().to_string())
    except Exception as exc:
        summary.update(status='failed',error=repr(exc));write(folder/'summary.json',summary);raise


if __name__=='__main__':main()
