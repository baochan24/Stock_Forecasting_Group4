"""Paired rolling-development experiment; never reads test targets or forwards test."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader,TensorDataset

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol
from backend.artifacts.scaler import save_scaler,load_scaler
from backend.data.transforms.scaling import scale,inverse_scale
from backend.data.transforms.anchored_price import encode_history,encode_targets,decode_prices,REPRESENTATION
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.models.cnn_one_step import CNNOneStep
from backend.experiments.management.experiment_manager import set_random_seed
from backend.training.trainer import train_model
from backend.evaluation.one_step import evaluate_one_step

PLAN='experiments/configs/tv6_residual_development_v1.json'


def write(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')


def select_records(records,targets,first,last):
    if len(records)!=len(targets):raise ValueError('Pair count')
    chosen=[]
    for x,y in zip(records,targets):
        if x['sample_id']!=y['sample_id']:raise ValueError('Pair IDs')
        if all(first<=d<=last for d in y['target_dates']):chosen.append((x,y))
    if not chosen:raise ValueError('Empty fold')
    return chosen


def arrays(pairs):
    return np.array([x['input_values'] for x,y in pairs],dtype=np.float64),np.array([y['target_values'] for x,y in pairs],dtype=np.float64)


def metrics(actual,predicted,pairs,context):
    rows=[];h=actual.shape[1]
    for step in list(range(h))+([-1] if h==5 else []):
        if step==-1:
            a=actual.reshape(-1,1);p=predicted.reshape(-1,1)
            keys=[(x['sample_id'],day) for x,y in pairs for day in y['target_dates']]
        else:
            a=actual[:,step:step+1];p=predicted[:,step:step+1]
            keys=[(x['sample_id'],y['target_dates'][step]) for x,y in pairs]
        score=evaluate_one_step(a,p,target_keys=keys,prediction_keys=keys)
        rows.append(dict(**context,horizon_step=None if step==-1 else step+1,scope='overall' if step==-1 else 'per_horizon',
            samples=len(pairs),error_count=len(a),mae_usd=score['mae_usd'],rmse_usd=score['rmse_usd'],bias_usd=float((p-a).mean())))
    return rows


def main():
    plan=json.loads((ROOT/PLAN).read_text())
    protocol=json.loads((ROOT/PROTOCOL_PATH).read_text())
    protocol_hash=validate_protocol(protocol,ROOT)
    watch=dict(protocol['semantic']['artifacts_sha256'])
    for name in [PLAN,PROTOCOL_PATH,'scripts/run_tv6_residual_development.py','backend/data/transforms/anchored_price.py',
                 'backend/training/trainer.py','backend/models/lstm_one_step/model.py','backend/models/lstm_multi_step/model.py',
                 'backend/models/cnn_one_step/model.py']:
        watch[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'logs/audit'/('tv6_residual_development_'+stamp);folder.mkdir()
    artifacts=ROOT/'artifacts/checkpoints'/folder.name;artifacts.mkdir()
    receipt=dict(status='running',passed=False,plan=plan,plan_sha256=watch[PLAN],original_protocol_sha256=protocol_hash,
        started_at_utc=datetime.now(timezone.utc).isoformat(),source_hashes=watch,post_test_development=True,
        test_inference_performed=False,test_metrics_calculated=False,python=platform.python_version(),torch=torch.__version__,runs=[])
    write(folder/'summary.json',receipt)
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    version=protocol['semantic']['dataset_version']
    inventory=json.loads((ROOT/'reports/audits/TV6_Input_Inventory.json').read_text())
    raw=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip')
    raw=raw[raw.date<='2023-12-31'].copy()  # No test target/metric/forward is used by this experiment.
    sources={}
    for cohort in protocol['semantic']['cohorts']:
        h=cohort['forecast_length'];base=ROOT/'data/prepared'/cohort['prepared_id']
        xx=[];yy=[]
        for split in ('train','val'):
            xx+=json.loads((base/f'f{h}_{split}_inputs.json').read_text())
            yy+=json.loads((base/f'f{h}_{split}_targets.json').read_text())
        sources[h]=(xx,yy)
    all_metrics=[];start=time.perf_counter()
    try:
        for year in plan['validation_years']:
            train_end=f'{year-1}-12-31'
            fit=raw[raw.date<=train_end]
            scaler=StandardScaler().fit(fit[['adjusted_close']].to_numpy())
            scaler_id=f'tv6_dev_prices_to_{year-1}_{stamp}'
            meta=dict(dataset_version=version,source_hashes=inventory['source_hashes'],fit_split='train',
                feature='adjusted_close',currency='USD',fit_first_date=fit.date.iloc[0],fit_last_date=fit.date.iloc[-1],
                fit_row_count=len(fit),development_fold_validation_year=year)
            sf=save_scaler(scaler,meta,ROOT/'artifacts/scalers',scaler_id)
            scaler,_=load_scaler(sf,expected_dataset_version=version,expected_source_hashes=inventory['source_hashes'])
            for task in plan['tasks']:
                h=5 if task.endswith('h5') else 1
                xx,yy=sources[h]
                train=select_records(xx,yy,'2015-01-01',train_end)
                val=select_records(xx,yy,f'{year}-01-01',f'{year}-12-31')
                if set(x['sample_id'] for x,y in train)&set(x['sample_id'] for x,y in val):raise ValueError('Overlapping folds')
                tx,ty=arrays(train);vx,vy=arrays(val)
                baseline=np.repeat(vx[:,-1,0,None],h,axis=1)
                all_metrics.extend(metrics(vy,baseline,val,dict(validation_year=year,task=task,representation='persistence',seed=None)))
                write(folder/f'fold_{year}_{task}.json',dict(train_samples=len(train),validation_samples=len(val),
                    train_first_target=train[0][1]['target_dates'][0],train_last_target=train[-1][1]['target_dates'][-1],
                    validation_first_target=val[0][1]['target_dates'][0],validation_last_target=val[-1][1]['target_dates'][-1],
                    scaler_id=scaler_id,scaler_scale=float(scaler.scale_[0]),scaler_fit=meta))
                for representation in plan['representations']:
                    residual=representation==REPRESENTATION
                    if residual:
                        x,a=encode_history(tx,scaler.scale_[0]);y=encode_targets(ty,a,scaler.scale_[0])
                        xv,av=encode_history(vx,scaler.scale_[0]);yv=encode_targets(vy,av,scaler.scale_[0])
                    else:
                        x=scale(tx,scaler);y=scale(ty,scaler);xv=scale(vx,scaler);yv=scale(vy,scaler)
                    for seed in plan['seeds']:
                        set_random_seed(seed)
                        model=CNNOneStep() if task=='cnn_h1' else (LSTMMultiStep() if h==5 else LSTMOneStep())
                        if residual:
                            head=model.head[-1] if task=='cnn_h1' else model.fc
                            torch.nn.init.zeros_(head.weight);torch.nn.init.zeros_(head.bias)
                        run_id=f'{year}_{task}_{"residual" if residual else "absolute"}_seed{seed}'
                        run_folder=folder/run_id;run_folder.mkdir()
                        def loader(a,b,shuffle):
                            return DataLoader(TensorDataset(torch.from_numpy(a),torch.from_numpy(b)),batch_size=32,
                                shuffle=shuffle,drop_last=False,generator=torch.Generator().manual_seed(seed))
                        def on_epoch(log):
                            pd.DataFrame(log).to_csv(run_folder/'epoch_logs.csv',index=False)
                        result=train_model(model,loader(x,y,True),loader(xv,yv,False),{'training':plan['training']},None,run_id,on_epoch=on_epoch)
                        model.eval()
                        with torch.inference_mode():
                            values=torch.cat([model(torch.from_numpy(xv[i:i+32])) for i in range(0,len(xv),32)]).numpy()
                        price=decode_prices(values,av,scaler.scale_[0]) if residual else inverse_scale(values,scaler)
                        context=dict(validation_year=year,task=task,representation=representation,seed=seed)
                        scores=metrics(vy,price,val,context);all_metrics.extend(scores)
                        checkpoint=artifacts/run_id;checkpoint.mkdir()
                        torch.save(model.state_dict(),checkpoint/'state_dict.pt')
                        state_hash=hashlib.sha256((checkpoint/'state_dict.pt').read_bytes()).hexdigest()
                        # Verify real file reload, not only RAM restore.
                        restored=CNNOneStep() if task=='cnn_h1' else (LSTMMultiStep() if h==5 else LSTMOneStep())
                        restored.load_state_dict(torch.load(checkpoint/'state_dict.pt',map_location='cpu',weights_only=True));restored.eval()
                        with torch.inference_mode():
                            np.testing.assert_array_equal(restored(torch.from_numpy(xv[:2])).numpy(),model(torch.from_numpy(xv[:2])).numpy())
                        manifest=dict(**context,representation_version=representation,dataset_version=version,scaler_id=scaler_id,
                            best_epoch=result['best_epoch'],best_val_loss=result['best_val_loss'],epochs=len(result['epoch_logs']),
                            train_samples=len(train),validation_samples=len(val),plan_sha256=watch[PLAN],source_hashes=watch,
                            purpose='post-test-development-not-release',checkpoint_sha256=state_hash,reload_verified=True)
                        write(checkpoint/'manifest.json',manifest)
                        records=[]
                        for i,(inp,target) in enumerate(val):
                            for k in range(h):
                                records.append(dict(sample_id=inp['sample_id'],forecast_origin=inp['forecast_origin'],target_date=target['target_dates'][k],
                                    horizon_step=k+1,actual_price=float(vy[i,k]),predicted_price=float(price[i,k]),baseline_price=float(baseline[i,k])))
                        pd.DataFrame(records).to_csv(run_folder/'validation_predictions.csv',index=False)
                        receipt['runs'].append(dict(**context,best_epoch=result['best_epoch'],epochs=len(result['epoch_logs']),
                            checkpoint=checkpoint.relative_to(ROOT).as_posix(),seconds=result['total_time_seconds']))
                        write(folder/'summary.json',receipt)
                        pd.DataFrame(all_metrics).to_csv(folder/'metrics.csv',index=False)
                        primary=scores[-1]
                        print(f'{run_id}: best={result["best_epoch"]} epochs={len(result["epoch_logs"])} MAE={primary["mae_usd"]:.4f} RMSE={primary["rmse_usd"]:.4f}',flush=True)
        for name,sha in watch.items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed source: '+name)
        validate_protocol(protocol,ROOT)
        if len(receipt['runs'])!=36:raise ValueError('Incomplete experiment')
        frame=pd.DataFrame(all_metrics)
        agg=frame[frame.representation!='persistence'].groupby(['validation_year','task','representation','scope','horizon_step'],dropna=False).agg(
            mae_mean=('mae_usd','mean'),mae_std=('mae_usd','std'),rmse_mean=('rmse_usd','mean'),rmse_std=('rmse_usd','std'),
            bias_mean=('bias_usd','mean'),seeds=('seed','count')).reset_index()
        agg.to_csv(folder/'aggregates.csv',index=False)
        receipt.update(status='completed',passed=True,total_seconds=time.perf_counter()-start,source_artifacts_unchanged=True,
            completed_at_utc=datetime.now(timezone.utc).isoformat(),runs_completed=len(receipt['runs']))
        write(folder/'summary.json',receipt)
        write(ROOT/'logs/audit/tv6_residual_development_latest.json',dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()))
        print(agg.to_string(index=False),flush=True)
        print(str(folder),flush=True)
    except Exception as exc:
        receipt.update(status='failed',error=repr(exc));write(folder/'summary.json',receipt);raise


if __name__=='__main__':main()
