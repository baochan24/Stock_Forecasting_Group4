"""Train-only drift reference and gradient instrumentation; no parameter updates."""
from copy import deepcopy
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
from backend.data.transforms.anchored_price import encode_history,encode_targets,REPRESENTATION
from backend.error_analysis.train_drift_reference import estimate_train_change,predict_train_change
from backend.error_analysis.lstm_diagnostics import describe
from backend.model_trace.gradient_diagnostics import trace_lstm_gradients
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep

PLAN='experiments/configs/tv6_lstm_learning_check_v1.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False),encoding='utf-8')


def main():
    plan=read(ROOT/PLAN);protocol=read(ROOT/PROTOCOL_PATH);protocol_sha=validate_protocol(protocol,ROOT)
    source=(ROOT/read(ROOT/'logs/audit/tv6_residual_development_latest.json')['evidence']).parent
    dev=read(source/'summary.json');audit=read(source/'independent_audit.json')
    if not dev['passed'] or not audit['passed']:raise ValueError('Unaccepted development source')
    watch=dict(dev['source_hashes'])
    for name,expected in audit['result_hashes'].items():
        path=source/name
        if sha(path)!=expected:raise ValueError('Changed development result')
        watch[path.relative_to(ROOT).as_posix()]=expected
    for name in [PLAN,'scripts/check_tv6_lstm_learning.py','backend/error_analysis/train_drift_reference.py',
            'backend/model_trace/gradient_diagnostics.py','tests/evaluation/test_train_drift_reference.py','tests/models/test_gradient_diagnostics.py']:
        watch[name]=sha(ROOT/name)
    for name,expected in watch.items():
        if sha(ROOT/name)!=expected:raise ValueError('Changed source '+name)
    folder=ROOT/'logs/audit'/('tv6_lstm_learning_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    summary=dict(passed=False,status='running',plan=plan,protocol_sha256=protocol_sha,source=str(source.relative_to(ROOT)),
        source_hashes=watch,weight_updates=False,training_run_performed=False,test_inference=False,
        diagnostic_backward_performed=True,train_reference_estimated=True)
    write(folder/'summary.json',summary)
    torch.set_num_threads(1)
    inventory=read(ROOT/'reports/audits/TV6_Input_Inventory.json');version=inventory['dataset_version']
    scores=[];predictions=[];gradient=[];input_gradient=[];changes=[];references=[]
    try:
        for year in plan['validation_years']:
            for h in plan['forecast_lengths']:
                cohort=next(c for c in protocol['semantic']['cohorts'] if c['forecast_length']==h)
                base=ROOT/'data/prepared'/cohort['prepared_id']
                tx=read(base/f'f{h}_train_inputs.json');ty=read(base/f'f{h}_train_targets.json')
                pairs=[(x,y) for x,y in zip(tx,ty) if all(d<=f'{year-1}-12-31' for d in y['target_dates'])]
                train_inputs=[x for x,y in pairs];train_targets=[y for x,y in pairs]
                reference=estimate_train_change(train_inputs,train_targets,dataset_version=version,train_last_date=f'{year-1}-12-31')
                references.append(dict(validation_year=year,**reference))
                split='train' if year==2022 else 'val'
                vx=read(base/f'f{h}_{split}_inputs.json');vy=read(base/f'f{h}_{split}_targets.json')
                val=[(x,y) for x,y in zip(vx,vy) if all(d.startswith(str(year)) for d in y['target_dates'])]
                raw=np.array([x['input_values'] for x,y in val],dtype=np.float64)
                def record(method,seed,price):
                    rows=[]
                    for i,(x,y) in enumerate(val):
                        if x['sample_id']!=y['sample_id']:raise ValueError('Validation pair mismatch')
                        for k in range(h):rows.append(dict(validation_year=year,forecast_length=h,method=method,seed=seed,
                            sample_id=x['sample_id'],target_date=y['target_dates'][k],horizon_step=k+1,
                            actual_price=float(y['target_values'][k]),origin_price=float(raw[i,-1,0]),predicted_price=float(price[i,k])))
                    frame=pd.DataFrame(rows);predictions.extend(rows)
                    for step in list(range(1,h+1))+([0] if h==5 else []):
                        g=frame if step==0 else frame[frame.horizon_step==step]
                        scores.append(dict(validation_year=year,forecast_length=h,method=method,seed=seed,
                            horizon_step=None if step==0 else step,metric_scope='overall' if step==0 else 'per_horizon',**describe(g)))
                record('persistence',None,np.repeat(raw[:,-1,0,None],h,axis=1))
                record('train_mean_change',None,predict_train_change(raw,reference))
                for seed in plan['seeds']:
                    run=next(r for r in dev['runs'] if r['validation_year']==year and r['task']==f'lstm_h{h}' and r['seed']==seed and r['representation']==REPRESENTATION)
                    checkpoint=ROOT/run['checkpoint'];manifest=read(checkpoint/'manifest.json')
                    if manifest['representation_version']!=REPRESENTATION or manifest['purpose']!='post-test-development-not-release':raise ValueError('Wrong representation')
                    for path in (checkpoint/'manifest.json',checkpoint/'state_dict.pt'):watch[path.relative_to(ROOT).as_posix()]=sha(path)
                    if sha(checkpoint/'state_dict.pt')!=manifest['checkpoint_sha256']:raise ValueError('Checkpoint hash')
                    sf=ROOT/'artifacts/scalers'/manifest['scaler_id']
                    scaler,sm=load_scaler(sf,expected_dataset_version=version,expected_source_hashes=inventory['source_hashes'])
                    if sm['metadata']['fit_last_date']>=f'{year}-01-01':raise ValueError('Scaler leakage')
                    for path in (sf/'manifest.json',sf/'scaler.json'):watch[path.relative_to(ROOT).as_posix()]=sha(path)
                    saved_path=source/f'{year}_lstm_h{h}_residual_seed{seed}'/'validation_predictions.csv'
                    watch[saved_path.relative_to(ROOT).as_posix()]=sha(saved_path)
                    saved=pd.read_csv(saved_path,float_precision='round_trip')
                    expected=[(x['sample_id'],d) for x,y in val for d in y['target_dates']]
                    if expected!=list(zip(saved.sample_id,saved.target_date)):raise ValueError('Different comparison cohort')
                    record('lstm_residual',seed,saved.predicted_price.to_numpy().reshape(len(val),h))
                    torch.manual_seed(seed)
                    initial=LSTMOneStep() if h==1 else LSTMMultiStep()
                    zero=deepcopy(initial);torch.nn.init.zeros_(zero.fc.weight);torch.nn.init.zeros_(zero.fc.bias)
                    model=LSTMOneStep() if h==1 else LSTMMultiStep()
                    model.load_state_dict(torch.load(checkpoint/'state_dict.pt',map_location='cpu',weights_only=True));model.eval()
                    original=deepcopy(model.state_dict())
                    delta_core=float(torch.sqrt(sum((p-zero.state_dict()[name]).square().sum() for name,p in original.items() if name.startswith('lstm.'))))
                    changes.append(dict(validation_year=year,forecast_length=h,seed=seed,best_epoch=run['best_epoch'],core_l2_change_from_reconstructed_init=delta_core,
                        head_weight_l2=float(model.fc.weight.detach().norm()),head_bias=model.fc.bias.detach().tolist(),
                        price_scale=float(scaler.scale_[0])))
                    train_raw=np.array([x['input_values'] for x,y in pairs],dtype=np.float64)
                    targets=np.array([y['target_values'] for x,y in pairs],dtype=np.float64)
                    encoded,anchors=encode_history(train_raw,scaler.scale_[0]);encoded_y=encode_targets(targets,anchors,scaler.scale_[0])
                    batches={'first32':slice(0,32),'middle32':slice(len(pairs)//2,len(pairs)//2+32),'last32':slice(-32,None)}
                    for state,current in [('reconstructed_zero_head_initialization',zero),('reconstructed_default_head_initialization',initial),('existing_checkpoint',model)]:
                        for batch,sl in batches.items():
                            result=trace_lstm_gradients(current,torch.from_numpy(encoded[sl]),torch.from_numpy(encoded_y[sl]))
                            per_session=result.pop('input_grad_l2_per_session')
                            context=dict(validation_year=year,forecast_length=h,seed=seed,state=state,batch=batch)
                            gradient.append(dict(**context,**result))
                            input_gradient.extend(dict(**context,session_position=i+1,gradient_l2=v) for i,v in enumerate(per_session))
                    if any(not torch.equal(original[name],value) for name,value in model.state_dict().items()) or any(p.grad is not None for p in model.parameters()):
                        raise ValueError('Caller model changed by gradient instrumentation')
        for name,expected in watch.items():
            if sha(ROOT/name)!=expected:raise ValueError('Changed source/artifact '+name)
        validate_protocol(protocol,ROOT)
        if len(gradient)!=108 or len(changes)!=12:raise ValueError('Missing gradient state/seed coverage')
        write(folder/'train_references.json',references)
        for name,rows in [('reference_metrics',scores),('reference_predictions',predictions),('gradient_norms',gradient),('input_gradient_by_session',input_gradient),('parameter_changes',changes)]:
            pd.DataFrame(rows).to_csv(folder/(name+'.csv'),index=False)
        summary.update(passed=True,status='completed',source_hashes=watch,models_checked=12,gradient_batches=108,
            references_estimated=4,source_artifacts_unchanged=True,limitations=[
                'Gradient probes describe selected training batches at reconstructed init/checkpoint; not historical optimizer trajectories',
                'Zero head blocks core only at initial backward; nonzero gradients alone do not establish predictive signal',
                'All performance comparisons are development, no new independent held-out claim'])
        write(folder/'summary.json',summary)
        write(ROOT/'logs/audit/tv6_lstm_learning_latest.json',dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()))
        primary=pd.DataFrame(scores);primary=primary[(primary.forecast_length==1)|(primary.metric_scope=='overall')]
        print(primary.groupby(['validation_year','forecast_length','method'])[['mae_usd','rmse_usd']].mean().to_string())
        g=pd.DataFrame(gradient)
        print(g.groupby('state')[['core_grad_l2','head_weight_grad_l2','head_bias_grad_l2']].mean().to_string())
        print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'))))
    except Exception as exc:
        summary.update(status='failed',error=repr(exc));write(folder/'summary.json',summary);raise


if __name__=='__main__':main()
