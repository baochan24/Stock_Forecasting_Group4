"""Bounded full train/validation smoke runs with CPU timing and disk reload."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time

import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.experiments.runner.aapl_factories import make_aapl_loaders, make_aapl_model
from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments
from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint


def main():
    folder = ROOT / 'logs/audit' / ('tv4_item6_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    torch.set_num_threads(1)
    rows = []
    for name in ['one_step', 'multi_step']:
        started = time.perf_counter()
        config = load_experiment_config(ROOT / f'experiments/configs/lstm_{name}_baseline.yaml')
        config['experiment_name'] = f'item6_smoke_{name}'
        config['seeds'] = [42]
        config['training']['max_epochs'] = 3
        config['acceptance_probe'] = {'scope': 'diagnostic full train/validation, three epochs'}
        config['output']['log_dir'] = str(folder / 'runs')
        config['output']['checkpoint_dir'] = str(ROOT / 'artifacts/checkpoints' / folder.name)
        path = folder / f'{name}.yaml'
        path.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
        train, val = make_aapl_loaders(config, 42, project_root=ROOT)
        models = []

        def factory(settings):
            model = make_aapl_model(settings)
            models.append(model)
            return model

        result, = run_experiments(path, factory, lambda settings, seed: (train, val))
        identity = train.dataset.provenance
        model, manifest = load_lstm_checkpoint(result['checkpoint_path'],
            expected_dataset_version=identity['dataset_version'], expected_source_hashes=identity['source_hashes'],
            expected_scaler_id=identity['scaler_id'], expected_forecast_length=config['data']['forecast_length'])
        with torch.inference_mode():
            squared = []
            for x, y, ids in val:
                prediction = model(x)
                torch.testing.assert_close(prediction, models[0](x), rtol=0, atol=0)
                squared.append((prediction - y).square())
            per_horizon = torch.cat(squared).mean(dim=0)
            assert math.isclose(per_horizon.mean().item(), result['best_val_loss'], rel_tol=1e-12)
            x, y, ids = next(iter(val))
            for _ in range(5):
                model(x)
            timings = []
            for _ in range(30):
                begin = time.perf_counter()
                model(x)
                timings.append(time.perf_counter() - begin)
        rows.append(dict(model=name, horizon=config['data']['forecast_length'], seed=42,
                         train_samples=len(train.dataset), val_samples=len(val.dataset),
                         parameters=sum(p.numel() for p in model.parameters()),
                         epochs=len(result['epoch_logs']), best_epoch=result['best_epoch'],
                         best_val_mse=result['best_val_loss'], val_mse_per_horizon=per_horizon.tolist(),
                         train_validation_seconds=result['total_time_seconds'],
                         train_seconds=sum(row['train_seconds'] for row in result['epoch_logs']),
                         validation_seconds=sum(row['validation_seconds'] for row in result['epoch_logs']),
                         inference_batch_samples=len(x), inference_repeats=30, warmup=5,
                         inference_batch_median_ms=statistics.median(timings)*1000,
                         total_seconds=time.perf_counter()-started, reload_equal=True,
                         run_dir=str(folder/'runs'/result['run_id']), checkpoint=result['checkpoint_path']))
    summary = dict(passed=True, scope='diagnostic three epochs, full train/validation',
                   cpu=platform.processor(), python=sys.version, torch=torch.__version__,
                   threads=torch.get_num_threads(), interop_threads=torch.get_num_interop_threads(),
                   dtype='float64', results=rows)
    evidence = folder / 'summary.json'
    evidence.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'evidence': str(evidence)}))


if __name__ == '__main__':
    main()
