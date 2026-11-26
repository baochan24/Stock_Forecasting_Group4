"""TV5 item9 validation USD comparison; test evaluation remains with TV6."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.cnn_checkpoint import PROVENANCE,fingerprint,load_cnn_checkpoint
from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint
from backend.artifacts.scaler import load_scaler
from backend.baselines.persistence import predict_persistence
from backend.data.transforms.scaling import inverse_scale
from backend.evaluation.one_step import evaluate_one_step
from backend.experiments.runner.cnn_factories import make_cnn_loaders
from backend.experiments.runner.experiment_runner import load_experiment_config
from backend.experiments.runner.cnn_plan import validate_official_plan


def main():
    torch.set_num_threads(1)
    cnn_path=sorted((ROOT/'logs/audit').glob('tv5_item8_*/summary.json'))[-1]
    cnn=json.loads(cnn_path.read_text())
    assert cnn['passed'] and cnn['seeds']==[42,123,456]
    config=load_experiment_config(cnn_path.parent/'official.yaml')
    validate_official_plan(config,json.loads((cnn_path.parent/'locked_plan.json').read_text()))
    _,val=make_cnn_loaders(config,42,project_root=ROOT)
    ds=val.dataset
    scaler,_=load_scaler(ROOT/'artifacts/scalers'/config['data']['scaler_id'],
        expected_dataset_version=config['data']['dataset_version'],expected_source_hashes=ds.provenance['source_hashes'])
    actual=inverse_scale(ds.y.numpy(),scaler)
    raw_x=inverse_scale(ds.X.numpy(),scaler)
    keys=list(zip(ds.sample_ids,[d[0] for d in ds.target_dates]))
    assert len(keys)==250 and all('2023-01-01'<=d<='2023-12-31' for _,d in keys)
    prepared=ROOT/'data/prepared'/config['data']['prepared_id']
    targets=json.loads((prepared/'f1_val_targets.json').read_text())
    assert keys==[(r['sample_id'],r['target_dates'][0]) for r in targets]
    np.testing.assert_allclose(actual,np.array([r['target_values'] for r in targets]),rtol=1e-12,atol=1e-12)
    inputs=json.loads((prepared/'f1_val_inputs.json').read_text())
    raw_baseline=predict_persistence(np.array([r['input_values'] for r in inputs]))
    np.testing.assert_allclose(predict_persistence(raw_x),raw_baseline,rtol=1e-12,atol=1e-12)
    folder=ROOT/'logs/audit'/('tv5_item9_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    sources=sorted({*ROOT.glob('backend/**/*.py'),Path(__file__)})
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    rows=[];predictions=[]
    def record(method,seed,pred,seconds=None,epochs=None,training_seconds=None,parameters=None):
        metric=evaluate_one_step(actual,pred,target_keys=keys,prediction_keys=keys)
        rows.append(dict(method=method,seed=seed,**metric,inference_median_seconds=seconds,
            epochs=epochs,historical_training_seconds=training_seconds,parameters=parameters))
        predictions.extend(dict(method=method,seed=seed,sample_id=k[0],target_date=k[1],
            actual_usd=float(a),predicted_usd=float(p),error_usd=float(p-a))
            for k,a,p in zip(keys,actual[:,0],pred[:,0]))
    times=[]
    for _ in range(20):
        start=time.perf_counter();predict_persistence(np.array([r['input_values'] for r in inputs]));times.append(time.perf_counter()-start)
    record('persistence',None,raw_baseline,float(np.median(times)),parameters=0)
    tv4root=ROOT/'logs/audit/tv4_item8_20261125T122649342552Z'
    lstm=json.loads((tv4root/'summary.json').read_text())
    candidates=[r for r in lstm['results'] if r['lookback']==30]
    assert [r['seed'] for r in candidates]==[42,123,456]
    checkpoint_hashes={}
    for method,results in [('CNN',cnn['results']),('LSTM',candidates)]:
        for row in results:
            seed=row['seed']
            if method=='CNN':
                path=ROOT/row['checkpoint_path']
                model,manifest=load_cnn_checkpoint(path,expected_provenance={k:ds.provenance[k] for k in PROVENANCE},
                    expected_model_config=config['model'],expected_training_config_sha256=fingerprint(config),expected_run_id=row['run_id'],expected_seed=seed)
                expected_mse=row['best_val_loss'];train_seconds=row['training_seconds']
            else:
                path=ROOT/'artifacts/checkpoints/tv4_item8_20261125T122649342552Z'/Path(row['checkpoint']).name
                model,manifest=load_lstm_checkpoint(path,expected_dataset_version=config['data']['dataset_version'],
                    expected_source_hashes=ds.provenance['source_hashes'],expected_scaler_id=config['data']['scaler_id'],
                    expected_forecast_length=1,expected_lookback=30)
                meta=json.loads((tv4root/'runs'/row['run_id']/'metadata.json').read_text())
                assert meta['config']['data']==config['data'] and meta['seed']==seed
                assert manifest['metadata']['run_id']==row['run_id'] and manifest['metadata']['seed']==seed
                expected_mse=row['validation_mse'];train_seconds=row['seconds']
            checkpoint_hashes[path.relative_to(ROOT).as_posix()]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (path/'manifest.json',path/'weights.pt')}
            with torch.inference_mode():
                def forward(): return torch.cat([model(x) for x,_,_ in val]).numpy()
                forward()  # warmup
                times=[]
                for _ in range(20):
                    start=time.perf_counter();scaled=forward();times.append(time.perf_counter()-start)
            assert np.isclose(np.mean((scaled-ds.y.numpy())**2),expected_mse,rtol=1e-12,atol=1e-14)
            record(method,seed,inverse_scale(scaled,scaler),float(np.median(times)),row['epochs'],train_seconds,
                   sum(p.numel() for p in model.parameters()))
    metrics=pd.DataFrame(rows)
    metrics.to_csv(folder/'metrics.csv',index=False)
    pd.DataFrame(predictions).to_csv(folder/'predictions_usd.csv',index=False)
    aggregates=[]
    for method in ('CNN','LSTM'):
        part=metrics[metrics.method==method]
        aggregates.append(dict(method=method,seeds=3,mae_usd_mean=float(part.mae_usd.mean()),
            mae_usd_std=float(part.mae_usd.std(ddof=1)),rmse_usd_mean=float(part.rmse_usd.mean()),
            rmse_usd_std=float(part.rmse_usd.std(ddof=1))))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    summary=dict(passed=True,split='validation',year=2023,samples=250,currency='USD',
        test_performance_evaluated=False,metrics=rows,aggregates=aggregates,std_ddof=1,
        ordered_keys_sha256=hashlib.sha256(json.dumps(keys).encode()).hexdigest(),
        cnn_evidence=cnn_path.relative_to(ROOT).as_posix(),lstm_evidence=(tv4root/'summary.json').relative_to(ROOT).as_posix(),
        source_hashes=hashes,checkpoint_hashes=checkpoint_hashes,source_unchanged=True,
        torch_threads=torch.get_num_threads(),inference_repeats=20,
        limitations=['Validation used for checkpoint selection; not final test evidence',
            'LSTM lookback selected from 10/30/60; CNN fixed Option A, unequal search budgets',
            'Historical training timings from different runs are descriptive, not controlled speed benchmarks',
            'Inference timing includes DataLoader for networks; persistence includes raw array construction'])
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),aggregates=aggregates)))


if __name__=='__main__': main()
