"""Freeze existing candidate; audit validation and post-development old-test evaluation.

No training, new architecture, refitting, hyperparameter or seed selection.
The old test has already informed development: never claim independent holdout.
"""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol,digest
from backend.artifacts.scaler import load_scaler
from backend.data.transforms.anchored_price import encode_history,decode_prices,REPRESENTATION
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.evaluation.one_step import evaluate_one_step

CONFIG='experiments/configs/tv6_lstm_residual_candidate_v1.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False),encoding='utf-8')


def candidate_catalog(dev,source):
    models=[];files={}
    for run in dev['runs']:
        if run['validation_year']!=2023 or not run['task'].startswith('lstm') or run['representation']!=REPRESENTATION:continue
        path=ROOT/run['checkpoint'];m=read(path/'manifest.json');h=5 if run['task']=='lstm_h5' else 1
        if (m['representation_version']!=REPRESENTATION or m['purpose']!='post-test-development-not-release'
                or m['validation_year']!=2023 or m['seed']!=run['seed']):raise ValueError('Candidate provenance')
        if sha(path/'state_dict.pt')!=m['checkpoint_sha256']:raise ValueError('Checkpoint checksum')
        models.append(dict(forecast_length=h,seed=run['seed'],checkpoint=run['checkpoint'],scaler_id=m['scaler_id'],
            best_epoch=m['best_epoch'],readout='last'))
        for p in [path/'manifest.json',path/'state_dict.pt',ROOT/'artifacts/scalers'/m['scaler_id']/'manifest.json',ROOT/'artifacts/scalers'/m['scaler_id']/'scaler.json']:
            files[p.relative_to(ROOT).as_posix()]=sha(p)
    if {(m['forecast_length'],m['seed']) for m in models}!={(h,s) for h in (1,5) for s in (42,123,456)} or len(models)!=6:
        raise ValueError('Expected all six candidates without seed selection')
    semantic=dict(candidate_id='tv6-lstm-residual-candidate-v1',stage='research-candidate-not-release',
        representation=REPRESENTATION,formula='predicted_price = last_observed_price + training_price_scale * model_output',
        lookback=30,dtype='float64',runtime='cpu-one-thread',dataset_version=models and read(ROOT/models[0]['checkpoint']/'manifest.json')['dataset_version'],
        models=models,artifacts_sha256=files,source_evidence=(source/'summary.json').relative_to(ROOT).as_posix(),
        evaluation_protocol=dict(validation_years=[2022,2023],test_period='2024-2025',
            test_label='post-development evaluation on previously observed test',independent_holdout=False,
            no_training=True,no_refit=True,no_tuning_after_results=True,all_seeds_required=True,
            metrics=['MAE_USD','RMSE_USD'],h5_overall='flatten sample x horizon errors',std_ddof=1,
            baseline='persistence on identical per-mode samples',new_test_inference_authorized_by='User requested completion without further training'))
    return dict(semantic=semantic,semantic_sha256=digest(semantic))


def score(actual,predicted,inputs,targets,context):
    h=actual.shape[1];rows=[]
    for k in list(range(h))+([-1] if h==5 else []):
        if k==-1:
            a=actual.reshape(-1,1);p=predicted.reshape(-1,1)
            keys=[(x['sample_id'],d) for x,y in zip(inputs,targets) for d in y['target_dates']]
        else:
            a=actual[:,k:k+1];p=predicted[:,k:k+1]
            keys=[(x['sample_id'],y['target_dates'][k]) for x,y in zip(inputs,targets)]
        m=evaluate_one_step(a,p,target_keys=keys,prediction_keys=keys)
        rows.append(dict(**context,horizon_step=None if k==-1 else k+1,metric_scope='overall' if k==-1 else 'per_horizon',
            sample_count=len(inputs),error_count=len(a),mae_usd=m['mae_usd'],rmse_usd=m['rmse_usd']))
    return rows


def forward_inputs(model,raw,scaler):
    encoded,anchor=encode_history(raw,scaler.scale_[0])
    with torch.inference_mode():
        delta=torch.cat([model(torch.from_numpy(encoded[i:i+32])) for i in range(0,len(encoded),32)]).numpy()
    return decode_prices(delta,anchor,scaler.scale_[0])


def main():
    protocol=read(ROOT/PROTOCOL_PATH);protocol_sha=validate_protocol(protocol,ROOT)
    source=(ROOT/read(ROOT/'logs/audit/tv6_residual_development_latest.json')['evidence']).parent
    dev=read(source/'summary.json');dev_audit=read(source/'independent_audit.json')
    if not dev['passed'] or not dev_audit['passed']:raise ValueError('Development not accepted')
    watch=dict(dev['source_hashes'])
    for name,expected in dev_audit['result_hashes'].items():
        if sha(source/name)!=expected:raise ValueError('Changed accepted development result')
        watch[(source/name).relative_to(ROOT).as_posix()]=expected
    cfg=candidate_catalog(dev,source)
    config_path=ROOT/CONFIG
    if config_path.exists():
        if read(config_path)!=cfg:raise ValueError('Candidate config immutable; refusing overwrite')
    else:
        with config_path.open('x',encoding='utf-8') as stream:json.dump(cfg,stream,indent=2,allow_nan=False)
    watch[CONFIG]=sha(config_path)
    for name in ['scripts/complete_tv6_lstm_candidate.py','backend/data/transforms/anchored_price.py',
                 'backend/models/lstm_one_step/model.py','backend/models/lstm_multi_step/model.py']:
        watch[name]=sha(ROOT/name)
    watch.update(cfg['semantic']['artifacts_sha256'])
    for name,expected in watch.items():
        if sha(ROOT/name)!=expected:raise ValueError('Changed source '+name)
    folder=ROOT/'logs/audit'/('tv6_lstm_completion_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    summary=dict(passed=False,status='running',candidate_sha256=cfg['semantic_sha256'],candidate_config=CONFIG,
        protocol_v1_sha256=protocol_sha,source_hashes=watch,training_performed=False,refit_performed=False,
        weights_changed=False,new_architecture=False,independent_holdout=False,
        test_label='post-development evaluation on previously observed test',test_exposure_possible=False,
        started_at_utc=datetime.now(timezone.utc).isoformat())
    write(folder/'execution.json',summary)  # Recorded after candidate lock, before any test forward.
    torch.set_num_threads(1)
    inventory=read(ROOT/'reports/audits/TV6_Input_Inventory.json');version=inventory['dataset_version']
    raw_table=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip').set_index('date').adjusted_close
    metrics=[];predictions=[];checks=[]
    try:
        with patch.object(StandardScaler,'fit',side_effect=RuntimeError('Refit forbidden')),patch.object(StandardScaler,'partial_fit',side_effect=RuntimeError('Refit forbidden')):
            for scope,year,split in [('development_2022',2022,'train'),('development_2023',2023,'val'),('post_development_test_2024_2025',2023,'test')]:
                for h in (1,5):
                    cohort=next(c for c in protocol['semantic']['cohorts'] if c['forecast_length']==h)
                    base=ROOT/'data/prepared'/cohort['prepared_id']
                    all_inputs=read(base/f'f{h}_{split}_inputs.json')
                    if split=='test':
                        inputs=all_inputs  # Do not load target values until all predictions for this mode exist.
                    else:
                        y=read(base/f'f{h}_{split}_targets.json')
                        inputs=[x for x,t in zip(all_inputs,y) if all(d.startswith(str(year)) for d in t['target_dates'])]
                    raw=np.array([x['input_values'] for x in inputs],dtype=np.float64)
                    for x in inputs:
                        dates=raw_table.index.tolist();i=dates.index(x['forecast_origin'])
                        if x['input_dates']!=dates[i-29:i+1]:raise ValueError('Input session sequence')
                        np.testing.assert_allclose(np.asarray(x['input_values'])[:,0],raw_table.iloc[i-29:i+1],rtol=0,atol=1e-12)
                    outputs={}
                    for seed in (42,123,456):
                        run=next(r for r in dev['runs'] if r['validation_year']==year and r['task']==f'lstm_h{h}' and r['seed']==seed and r['representation']==REPRESENTATION)
                        path=ROOT/run['checkpoint'];m=read(path/'manifest.json')
                        for p in (path/'manifest.json',path/'state_dict.pt'):watch[p.relative_to(ROOT).as_posix()]=sha(p)
                        if sha(path/'state_dict.pt')!=m['checkpoint_sha256']:raise ValueError('Checkpoint hash')
                        scaler,sm=load_scaler(ROOT/'artifacts/scalers'/m['scaler_id'],expected_dataset_version=version,expected_source_hashes=inventory['source_hashes'])
                        if sm['metadata']['fit_last_date']>=f'{year}-01-01':raise ValueError('Scaler fit leaks validation/test')
                        model=LSTMOneStep() if h==1 else LSTMMultiStep()
                        model.load_state_dict(torch.load(path/'state_dict.pt',weights_only=True,map_location='cpu'));model.eval()
                        for p in model.parameters():p.requires_grad_(False)
                        before={k:v.clone() for k,v in model.state_dict().items()}
                        if split=='test':summary['test_exposure_possible']=True;write(folder/'execution.json',summary)
                        values=forward_inputs(model,raw,scaler)
                        # Last observation is the anchor; verify output independent of batch partitioning at both boundaries.
                        for i in (0,len(inputs)-1):np.testing.assert_allclose(values[i:i+1],forward_inputs(model,raw[i:i+1],scaler),rtol=0,atol=1e-12)
                        if any(not torch.equal(before[k],v) for k,v in model.state_dict().items()) or any(p.grad is not None for p in model.parameters()):
                            raise ValueError('Inference changed weights/gradients')
                        if split!='test':
                            saved=source/f'{year}_lstm_h{h}_residual_seed{seed}'/'validation_predictions.csv'
                            watch[saved.relative_to(ROOT).as_posix()]=sha(saved)
                            old=pd.read_csv(saved,float_precision='round_trip')
                            np.testing.assert_allclose(values.reshape(-1),old.predicted_price,rtol=0,atol=1e-12)
                        outputs[seed]=values
                        checks.append(dict(scope=scope,forecast_length=h,seed=seed,input_samples=len(inputs),checkpoint=run['checkpoint'],
                            batch_tail=len(inputs)%32,boundary_single_sample_matches=True,source_validation_predictions_match=split!='test',
                            dtype='float64',no_grad=True,weights_unchanged=True))
                    # Actuals are joined after input-only model inference, not passed to forward_inputs.
                    targets=read(base/f'f{h}_{split}_targets.json')
                    if split!='test':targets=[t for t in targets if all(d.startswith(str(year)) for d in t['target_dates'])]
                    if len(inputs)!=len(targets) or any(x['sample_id']!=t['sample_id'] for x,t in zip(inputs,targets)):raise ValueError('Actual pairing')
                    if split=='test':
                        keys=[dict(sample_id=x['sample_id'],forecast_origin=x['forecast_origin'],target_dates=t['target_dates']) for x,t in zip(inputs,targets)]
                        if len(keys)!=cohort['samples'] or digest(keys)!=cohort['ordered_keys_sha256']:raise ValueError('Full-test cohort mismatch')
                    actual=np.array([t['target_values'] for t in targets],dtype=np.float64)
                    np.testing.assert_allclose(actual.reshape(-1),[raw_table[d] for t in targets for d in t['target_dates']],rtol=0,atol=1e-12)
                    baseline=np.repeat(raw[:,-1,0,None],h,axis=1)
                    for method,seed,price in [('persistence',None,baseline)]+[('lstm_residual',seed,values) for seed,values in outputs.items()]:
                        metrics.extend(score(actual,price,inputs,targets,dict(scope=scope,forecast_length=h,method=method,seed=seed)))
                        for i,(x,t) in enumerate(zip(inputs,targets)):
                            for k in range(h):predictions.append(dict(scope=scope,forecast_length=h,method=method,seed=seed,sample_id=x['sample_id'],
                                forecast_origin=x['forecast_origin'],target_date=t['target_dates'][k],horizon_step=k+1,
                                actual_price=float(actual[i,k]),predicted_price=float(price[i,k]),origin_price=float(raw[i,-1,0])))
        for name,expected in watch.items():
            if sha(ROOT/name)!=expected:raise ValueError('Changed source '+name)
        validate_protocol(protocol,ROOT)
        frame=pd.DataFrame(metrics)
        aggregate=frame[frame.method=='lstm_residual'].groupby(['scope','forecast_length','horizon_step','metric_scope'],dropna=False).agg(
            mae_mean=('mae_usd','mean'),mae_std=('mae_usd','std'),rmse_mean=('rmse_usd','mean'),rmse_std=('rmse_usd','std'),seeds=('seed','count')).reset_index()
        frame.to_csv(folder/'metrics.csv',index=False);aggregate.to_csv(folder/'aggregates.csv',index=False)
        pd.DataFrame(predictions).to_csv(folder/'predictions.csv',index=False);pd.DataFrame(checks).to_csv(folder/'pipeline_checks.csv',index=False)
        summary.update(passed=True,status='completed',source_hashes=watch,pipeline_checks=len(checks),candidate_models=6,
            test_evaluated=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),
            conclusion='Candidate frozen for handoff; old test evaluation is post-development, not independent evidence')
        write(folder/'execution.json',summary);write(folder/'summary.json',summary)
        write(ROOT/'logs/audit/tv6_lstm_completion_latest.json',dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()))
        print(aggregate[(aggregate.forecast_length==1)|(aggregate.metric_scope=='overall')].to_string(index=False))
        print(frame[(frame.scope=='post_development_test_2024_2025')&(frame.method=='persistence')].to_string(index=False))
        print(str(folder))
    except Exception as exc:
        summary.update(status='failed',error=repr(exc));write(folder/'execution.json',summary);raise


if __name__=='__main__':main()
