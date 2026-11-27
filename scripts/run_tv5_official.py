"""Three locked Option A CNN runs. Validation selection only, no test metrics."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import torch
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.cnn_checkpoint import PROVENANCE,fingerprint,load_cnn_checkpoint
from backend.experiments.runner.cnn_factories import make_cnn_loaders,make_cnn_model
from backend.experiments.runner.cnn_plan import validate_official_plan
from backend.experiments.runner.experiment_runner import load_experiment_config,run_experiments
from backend.training.trainer import _run_epoch


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    torch.set_num_threads(1)
    folder=ROOT/'logs/audit'/('tv5_item8_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    baseline=ROOT/'experiments/configs/cnn_one_step_baseline.yaml'
    lock_path=ROOT/'experiments/configs/cnn_one_step_option_a.lock.json'
    plan=json.loads(lock_path.read_text())
    assert sha(baseline)==plan['baseline_yaml_sha256']
    config=load_experiment_config(baseline)
    semantic_hash=validate_official_plan(config,plan)
    config['output']=dict(checkpoint_dir=(folder/'checkpoints').relative_to(ROOT).as_posix(),
                          log_dir=(folder/'runs').relative_to(ROOT).as_posix())
    validate_official_plan(config,plan)
    path=folder/'official.yaml'
    path.write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    (folder/'locked_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    sources=sorted({*ROOT.glob('backend/**/*.py'),Path(__file__),baseline,lock_path,path})
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    (folder/'preflight.json').write_text(json.dumps(dict(passed=True,purpose='research',
        semantic_sha256=semantic_hash,seeds=config['seeds'],epoch_cap=300,source_hashes=hashes),indent=2))
    models=[]
    initials=[]
    def factory(c):
        model=make_cnn_model(c)
        models.append(model)
        initials.append({k:v.clone() for k,v in model.state_dict().items()})
        return model
    def loaders(c,seed):
        validate_official_plan(c,plan)
        print(json.dumps(dict(event='starting_seed',seed=seed)),flush=True)
        return make_cnn_loaders(c,seed,project_root=ROOT)
    wall,cpu=time.perf_counter(),time.process_time()
    results=run_experiments(str(path),model_factory=factory,dataloader_factory=loaders,checkpoint_purpose='research')
    timings=dict(runner_wall_seconds=time.perf_counter()-wall,process_cpu_seconds=time.process_time()-cpu)
    assert [r['seed'] for r in results]==[42,123,456]
    train,val=make_cnn_loaders(config,42,project_root=ROOT)
    rows=[]
    for result,model,initial in zip(results,models,initials):
        seed=result['seed']
        history=pd.DataFrame(result['epoch_logs'])
        assert 1<=len(history)<=100
        assert np.isfinite(history[['train_loss','val_loss','time_seconds']].to_numpy()).all()
        best=history.loc[history.val_loss.idxmin()]
        assert int(best.epoch)==result['best_epoch'] and best.val_loss==result['best_val_loss']
        history.to_csv(folder/f'history_seed{seed}.csv',index=False)
        args=dict(expected_provenance={k:train.dataset.provenance[k] for k in PROVENANCE},
            expected_model_config=config['model'],expected_training_config_sha256=fingerprint(config),
            expected_run_id=result['run_id'],expected_seed=seed)
        restored,manifest=load_cnn_checkpoint(result['checkpoint_path'],**args)
        assert manifest['metadata']['trained'] and manifest['metadata']['purpose']=='research'
        loss=_run_epoch(restored,val,torch.nn.MSELoss())
        assert np.isclose(loss,result['best_val_loss'],rtol=1e-12,atol=1e-14)
        assert all(torch.isfinite(p).all() for p in restored.parameters())
        assert any(not torch.equal(v,initial[k]) for k,v in model.state_dict().items())
        predictions=[]
        with torch.inference_mode():
            for x,y,ids in val:
                a,b=model(x),restored(x)
                torch.testing.assert_close(a,b,rtol=0,atol=0)
                predictions.extend(dict(sample_id=i,target_scaled=t,prediction_scaled=p,reload_abs_diff=abs(p-q))
                    for i,t,p,q in zip(ids,y[:,0].tolist(),a[:,0].tolist(),b[:,0].tolist()))
        pd.DataFrame(predictions).to_csv(folder/f'validation_scaled_seed{seed}.csv',index=False)
        metadata=json.loads((folder/'runs'/result['run_id']/'metadata.json').read_text())
        assert metadata['status']=='completed' and metadata['config']==config
        rows.append(dict(seed=seed,run_id=result['run_id'],epochs=len(history),best_epoch=result['best_epoch'],
            best_val_loss=result['best_val_loss'],reload_val_loss=loss,reload_predictions_exact=True,
            early_stopped=result['early_stopped'],training_seconds=result['total_time_seconds'],
            train_seconds=float(history.train_seconds.sum()),validation_seconds=float(history.validation_seconds.sum()),
            checkpoint_path=Path(result['checkpoint_path']).relative_to(ROOT).as_posix()))
        print(json.dumps(dict(event='verified_seed',**rows[-1])),flush=True)
    frame=pd.DataFrame(rows)
    assert frame.epochs.sum()<=300 and all(sha(ROOT/name)==value for name,value in hashes.items())
    frame.to_csv(folder/'results.csv',index=False)
    values=frame.best_val_loss.to_numpy()
    summary=dict(passed=True,purpose='research',test_performance_evaluated=False,seeds=[42,123,456],
        results=rows,total_epochs=int(frame.epochs.sum()),epoch_cap=300,semantic_sha256=semantic_hash,
        config_sha256=fingerprint(config),validation_mse_mean=float(values.mean()),
        validation_mse_std=float(values.std(ddof=1)),std_ddof=1,parameters=17057,dtype='float64',device='cpu',
        samples=dict(train=len(train.dataset),validation=len(val.dataset)),timing=timings,
        torch_threads=torch.get_num_threads(),torch_interop_threads=torch.get_num_interop_threads(),
        python=sys.version,torch=torch.__version__,source_hashes=hashes,source_unchanged=True,
        selected_seed=None,selection='best validation epoch per seed; retain all three seeds')
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'))),flush=True)


if __name__=='__main__': main()
