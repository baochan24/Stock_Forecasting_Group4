"""TV6 item1 intake only: hashes, provenance, history and input-only reload probes."""
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
from backend.artifacts.cnn_checkpoint import PROVENANCE,fingerprint,load_cnn_checkpoint
from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint
from backend.experiments.runner.aapl_factories import make_aapl_loaders
from backend.experiments.runner.cnn_plan import validate_official_plan
from backend.experiments.runner.experiment_runner import load_experiment_config
from backend.data.preparation.snapshot import load_tv1_snapshot


def main():
    torch.set_num_threads(1)
    output=ROOT/'logs/audit'/('tv6_item1_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(parents=True)
    inventory={};models=[];coverage=[]
    def track(path):
        path=Path(path).resolve()
        assert path.is_relative_to(ROOT)
        inventory[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    base4=ROOT/'logs/audit/tv4_item8_20261125T122649342552Z'
    base5=ROOT/'logs/audit/tv4_item9_20261125T140320407544Z'
    cnn_path=ROOT/'logs/audit/tv5_item8_20261126T044554616259Z/summary.json'
    csummary=json.loads(cnn_path.read_text());assert csummary['passed'] and not csummary['test_performance_evaluated']
    for name,expected in csummary['source_hashes'].items():
        path=ROOT/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
        track(path)
    cnn_config=load_experiment_config(cnn_path.parent/'official.yaml')
    plan=json.loads((ROOT/'experiments/configs/cnn_one_step_option_a.lock.json').read_text())
    validate_official_plan(cnn_config,plan)
    snap=load_tv1_snapshot(ROOT,cnn_config['data']['dataset_version'])
    for path in snap['paths'].values():track(path)
    source_hashes=snap['acceptance']['hashes']
    configs={};loaders={}
    lstm_groups=[]
    for base,h in [(base4,1),(base5,5)]:
        summary=json.loads((base/'summary.json').read_text());assert summary['passed']
        if h==1: assert summary['selected_lookback']==30
        rows=[r for r in summary['results'] if r['lookback']==30]
        assert [r['seed'] for r in rows]==[42,123,456]
        first=json.loads((base/'runs'/rows[0]['run_id']/'metadata.json').read_text())
        config=first['config'];configs[h]=config
        assert config['data']['dataset_version']==snap['dataset_version']
        loaders[h]=make_aapl_loaders(config,42,project_root=ROOT)
        lstm_groups.append((base,h,rows))
        track(base/'summary.json')
        for split,loader in zip(['train','val'],loaders[h]):
            ds=loader.dataset
            assert ds.provenance['source_hashes']==source_hashes
            coverage.append(dict(forecast_length=h,split=split,samples=len(ds),input_shape=list(ds.X.shape),
                target_shape=list(ds.y.shape),first_target=ds.target_dates[0][0],last_target=ds.target_dates[-1][-1],
                ordered_ids_sha256=hashlib.sha256('\n'.join(ds.sample_ids).encode()).hexdigest()))
        prepared=ROOT/'data/prepared'/config['data']['prepared_id']
        for file in prepared.glob('*'):
            if file.is_file():track(file)
        # Count test windows without calling model or evaluating target errors.
        with np.load(prepared/f'f{h}_test.npz',allow_pickle=False) as a:
            coverage.append(dict(forecast_length=h,split='test_schema_only',samples=len(a['X']),
                input_shape=list(a['X'].shape),target_shape=list(a['y'].shape)))
    assert cnn_config['data']==configs[1]['data']
    provenance=loaders[1][0].dataset.provenance
    for file in (ROOT/'artifacts/scalers'/provenance['scaler_id']).glob('*'):
        if file.is_file():track(file)
    def selection(row,folder,run_dir,h,method,config):
        meta=json.loads((run_dir/'metadata.json').read_text())
        checkpoint=json.loads((folder/'manifest.json').read_text())
        assert meta['status']=='completed' and meta['seed']==row['seed'] and meta['run_id']==row['run_id']
        assert meta['config']==config and checkpoint['metadata']['training_config']==config
        assert checkpoint['metadata']['source_hashes']==source_hashes
        assert checkpoint['metadata']['run_id']==row['run_id'] and checkpoint['metadata']['seed']==row['seed']
        assert checkpoint['metadata']['trained'] and checkpoint['metadata']['selected_on']=='validation'
        hist=pd.read_csv(run_dir/'epoch_logs.csv')
        assert hist.epoch.tolist()==list(range(1,len(hist)+1)) and 1<=len(hist)<=100
        assert np.isfinite(hist[['train_loss','val_loss']].to_numpy()).all()
        best=hist.loc[hist.val_loss.idxmin()]
        assert int(best.epoch)==checkpoint['metadata']['best_epoch']==row['best_epoch']
        assert np.isclose(best.val_loss,checkpoint['metadata']['best_val_loss'],rtol=1e-12,atol=1e-14)
        for file in [folder/'manifest.json',folder/'weights.pt',run_dir/'metadata.json',run_dir/'epoch_logs.csv']:track(file)
        return dict(method=method,forecast_length=h,lookback=30,seed=row['seed'],run_id=row['run_id'],
            best_epoch=row['best_epoch'],checkpoint=folder.relative_to(ROOT).as_posix(),
            prepared_id=config['data']['prepared_id'],scaler_id=config['data']['scaler_id'],
            history_verified=True,probe_split='validation_inputs_only')
    for base,h,rows in lstm_groups:
        for row in rows:
            folder=ROOT/'artifacts/checkpoints'/base.name/Path(row['checkpoint']).name
            run_dir=base/'runs'/row['run_id'];config=json.loads((run_dir/'metadata.json').read_text())['config']
            assert config['data']==configs[h]['data']
            model,_=load_lstm_checkpoint(folder,expected_dataset_version=snap['dataset_version'],
                expected_source_hashes=source_hashes,expected_scaler_id=provenance['scaler_id'],
                expected_forecast_length=h,expected_lookback=30)
            with torch.inference_mode():pred=model(loaders[h][1].dataset.X[:2])
            assert pred.shape==(2,h) and torch.isfinite(pred).all()
            entry=selection(row,folder,run_dir,h,'LSTM',config);entry['parameters']=sum(p.numel() for p in model.parameters())
            models.append(entry)
    for row in csummary['results']:
        folder=ROOT/row['checkpoint_path'];run_dir=cnn_path.parent/'runs'/row['run_id']
        model,_=load_cnn_checkpoint(folder,expected_provenance={k:provenance[k] for k in PROVENANCE},
            expected_model_config=cnn_config['model'],expected_training_config_sha256=fingerprint(cnn_config),
            expected_run_id=row['run_id'],expected_seed=row['seed'])
        with torch.inference_mode():pred=model(loaders[1][1].dataset.X[:2])
        assert pred.shape==(2,1) and torch.isfinite(pred).all()
        entry=selection(row,folder,run_dir,1,'CNN',cnn_config);entry['parameters']=model.count_parameters();models.append(entry)
    for path in [cnn_path,cnn_path.parent/'official.yaml',ROOT/'experiments/configs/cnn_one_step_option_a.lock.json']:track(path)
    assert len(models)==9
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in inventory.items())
    result=dict(passed=True,scope='TV6 item1 local input acceptance, not final evaluation or release',
        dataset_version=snap['dataset_version'],snapshot_rows=len(snap['data']),source_hashes=source_hashes,
        models=models,coverage=coverage,files=inventory,source_data_unchanged=True,
        test_performance_evaluated=False,trained_again=False,release_selected=False,
        pending=['item2 final evaluation protocol and demo model selection rule',
                 'items3-10 inference/evaluation/test/release/API/frontend/final handoff',
                 'recipient machine verification and historical peak RAM'],
        python=sys.version,torch=torch.__version__)
    path=output/'inventory.json';path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    (ROOT/'logs/audit/tv6_item1_latest.json').write_text(json.dumps(dict(passed=True,evidence=path.relative_to(ROOT).as_posix()),indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,evidence=str(path),models=9,files=len(inventory))))


if __name__=='__main__':main()
