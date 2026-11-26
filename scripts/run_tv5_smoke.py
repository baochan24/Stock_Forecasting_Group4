"""Five-epoch AAPL CNN diagnostic through the shared runner; never evaluate test."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.artifacts.cnn_checkpoint import PROVENANCE, fingerprint, load_cnn_checkpoint
from backend.experiments.runner.cnn_factories import make_cnn_loaders, make_cnn_model
from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments
from backend.training.trainer import _run_epoch


def main():
    torch.set_num_threads(1)
    folder = ROOT / 'logs/audit' / ('tv5_item7_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    baseline_path = ROOT / 'experiments/configs/cnn_one_step_baseline.yaml'
    baseline_hash = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    config = load_experiment_config(baseline_path)
    assert config['seeds'] == [42,123,456] and config['training']['max_epochs'] == 100
    assert config['model'] == dict(lookback=30,n_features=1,conv1_channels=16,conv2_channels=32,
        kernel_size=3,pool_size=2,hidden_units=32,dropout=.1,output_size=1)
    config['experiment_name'] = 'cnn_aapl_smoke_diagnostic_5epochs'
    config['seeds'] = [42]
    config['training']['max_epochs'] = 5
    config['output'] = dict(checkpoint_dir=(folder/'checkpoints').relative_to(ROOT).as_posix(),
                            log_dir=(folder/'runs').relative_to(ROOT).as_posix())
    config_path = folder / 'smoke.yaml'
    config_path.write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    train, val = make_cnn_loaders(config,42,project_root=ROOT)
    assert len(train.dataset) == 1954 and len(val.dataset) == 250
    pinned = [ROOT/'artifacts/scalers'/config['data']['scaler_id']/'manifest.json',
              ROOT/'data/prepared'/config['data']['prepared_id']/'manifest.json']
    data_hashes = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned}
    captured, handles = {}, []
    stats = dict(train_batches=0,validation_batches=0,train_samples=0,validation_samples=0,
                 validation_grad_enabled=False,gradient_tensors=0,max_abs_gradient=0.)
    def factory(c):
        model = make_cnn_model(c)
        captured['model'] = model
        captured['initial'] = {k:v.clone() for k,v in model.state_dict().items()}
        def observe(m, args):
            prefix = 'train' if m.training else 'validation'
            stats[prefix+'_batches'] += 1
            stats[prefix+'_samples'] += len(args[0])
            if not m.training:
                stats['validation_grad_enabled'] |= torch.is_grad_enabled()
        handles.append(model.register_forward_pre_hook(observe))
        def gradient(grad):
            assert torch.isfinite(grad).all()
            stats['gradient_tensors'] += 1
            stats['max_abs_gradient'] = max(stats['max_abs_gradient'],grad.abs().max().item())
        for p in model.parameters():
            handles.append(p.register_hook(gradient))
        return model
    wall, cpu = time.perf_counter(), time.process_time()
    result = run_experiments(str(config_path),model_factory=factory,
        dataloader_factory=lambda c,s:(train,val),checkpoint_purpose='diagnostic')[0]
    timing = dict(runner_wall_seconds=time.perf_counter()-wall,process_cpu_seconds=time.process_time()-cpu,
                  training_loop_seconds=result['total_time_seconds'],torch_threads=torch.get_num_threads())
    for handle in handles: handle.remove()
    epochs = len(result['epoch_logs'])
    assert 1 <= epochs <= 5
    assert stats['train_samples'] == epochs*len(train.dataset)
    assert stats['validation_samples'] == epochs*len(val.dataset)
    assert stats['train_batches'] == epochs*len(train) and stats['validation_batches'] == epochs*len(val)
    assert stats['gradient_tensors'] > 0 and not stats['validation_grad_enabled']
    model = captured['model'].eval()
    assert all(torch.isfinite(p).all() for p in model.parameters())
    assert any(not torch.equal(v,captured['initial'][k]) for k,v in model.state_dict().items())
    args = dict(expected_provenance={k:train.dataset.provenance[k] for k in PROVENANCE},
        expected_model_config=config['model'],expected_training_config_sha256=fingerprint(config),
        expected_run_id=result['run_id'],expected_seed=42)
    try:
        load_cnn_checkpoint(result['checkpoint_path'],**args)
    except ValueError as exc:
        assert 'Diagnostic' in str(exc)
        rejection = str(exc)
    else:
        raise AssertionError('Diagnostic must be rejected by default')
    restored, manifest = load_cnn_checkpoint(result['checkpoint_path'],**args,allow_diagnostic=True)
    reload_loss = _run_epoch(restored,val,torch.nn.MSELoss())
    assert np.isclose(reload_loss,result['best_val_loss'],rtol=1e-12,atol=1e-14)
    predictions = []
    with torch.inference_mode():
        for x,y,ids in val:
            a,b = model(x),restored(x)
            torch.testing.assert_close(a,b,rtol=0,atol=0)
            predictions.extend(dict(sample_id=i,target_scaled=t,prediction_scaled=p,reload_abs_diff=abs(p-q))
                for i,t,p,q in zip(ids,y[:,0].tolist(),a[:,0].tolist(),b[:,0].tolist()))
    history = pd.DataFrame(result['epoch_logs'])
    assert np.isfinite(history[['train_loss','val_loss','time_seconds']].to_numpy()).all()
    history.to_csv(folder/'history.csv',index=False)
    pd.DataFrame(predictions).to_csv(folder/'validation_scaled.csv',index=False)
    assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == baseline_hash
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in data_hashes.items())
    summary = dict(passed=True,purpose='diagnostic',aapl_training=True,test_performance_evaluated=False,
        epochs=epochs,seed=42,samples=dict(train=len(train.dataset),validation=len(val.dataset)),
        batches=dict(train=len(train),validation=len(val)),tail=dict(train=2,validation=26),
        best_epoch=result['best_epoch'],best_val_loss=result['best_val_loss'],reload_val_loss=reload_loss,
        reload_predictions_exact=True,default_diagnostic_rejection=rejection,finite_weights=True,
        weights_changed=True,gradient_stats=stats,timing=timing,parameters=model.count_parameters(),
        dtype='float64',device='cpu',checkpoint_path=Path(result['checkpoint_path']).relative_to(ROOT).as_posix(),
        manifest=manifest,config_sha256=fingerprint(config),baseline_yaml_sha256=baseline_hash,
        data_manifests_unchanged=True,python=sys.version,torch=torch.__version__)
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'))))


if __name__ == '__main__': main()
