"""Execute the locked nine-run one-step grid and verify every selected checkpoint."""
from datetime import datetime, timezone
import json
import argparse
import math
from pathlib import Path
import sys

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments
from backend.experiments.runner.aapl_factories import make_aapl_loaders
from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--five-step', action='store_true')
    parser.add_argument('--plan-dir', type=Path, default=ROOT / 'logs/audit/tv4_item7_20261125T120957429763Z')
    args = parser.parse_args()
    horizon = 5 if args.five_step else 1
    lookbacks = (30,) if args.five_step else (10,30,60)
    folder = ROOT / 'logs/audit' / (('tv4_item9_' if args.five_step else 'tv4_item8_') + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    plan = args.plan_dir.resolve()
    summary = dict(passed=False, status='running', results=[])
    evidence = folder / 'summary.json'

    def record():
        evidence.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    record()
    torch.set_num_threads(1)
    try:
        for lookback in lookbacks:
            config = load_experiment_config(plan / ('five_step_lb30.yaml' if args.five_step else f'one_step_lb{lookback}.yaml'))
            assert config['seeds'] == [42,123,456] and config['training']['max_epochs'] == 100
            config['output']['log_dir'] = str(folder / 'runs')
            config['output']['checkpoint_dir'] = str(ROOT / 'artifacts/checkpoints' / folder.name)
            path = folder / f'lb{lookback}.yaml'
            path.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
            loaders = make_aapl_loaders(config, 42, project_root=ROOT)
            for result in run_experiments(path, dataloader_factory=lambda settings, seed: loaders):
                identity = loaders[1].dataset.provenance
                model, manifest = load_lstm_checkpoint(result['checkpoint_path'],
                    expected_dataset_version=identity['dataset_version'], expected_source_hashes=identity['source_hashes'],
                    expected_scaler_id=identity['scaler_id'], expected_forecast_length=horizon, expected_lookback=lookback)
                with torch.inference_mode():
                    errors = [(model(x)-y).square() for x,y,ids in loaders[1]]
                    per_horizon = torch.cat(errors).mean(dim=0)
                    actual = per_horizon.mean().item()
                assert math.isclose(actual,result['best_val_loss'],rel_tol=1e-12)
                logs = result['epoch_logs']
                assert result['best_epoch'] == min(logs,key=lambda row:row['val_loss'])['epoch']
                recorded = logs[result['best_epoch']-1]['val_mse_per_horizon']
                np.testing.assert_allclose(per_horizon.numpy(),recorded,rtol=1e-12,atol=1e-14)
                assert len(logs) == 100 or (result['early_stopped'] and len(logs)-result['best_epoch']==10)
                row = dict(lookback=lookback,horizon=horizon,seed=result['seed'],run_id=result['run_id'],
                           epochs=len(logs),best_epoch=result['best_epoch'],validation_mse=actual,
                           validation_mse_per_horizon=per_horizon.tolist(),
                           seconds=result['total_time_seconds'],checkpoint=result['checkpoint_path'],
                           run_dir=str(folder/'runs'/result['run_id']),reload_verified=True)
                summary['results'].append(row)
                record()
                print(json.dumps(row),flush=True)
        aggregates = []
        for lookback in lookbacks:
            values = [r['validation_mse'] for r in summary['results'] if r['lookback']==lookback]
            assert len(values)==3
            aggregates.append(dict(lookback=lookback,mean_validation_mse=float(np.mean(values)),
                                   sample_std=float(np.std(values,ddof=1))))
        summary.update(passed=True,status='completed',aggregates=aggregates,
                       selected_lookback=min(aggregates,key=lambda r:(r['mean_validation_mse'],r['lookback']))['lookback'])
    except (Exception,KeyboardInterrupt) as exc:
        summary.update(status='failed',error=dict(type=type(exc).__name__,message=str(exc)))
        raise
    finally:
        record()
    print(json.dumps({'evidence':str(evidence)}),flush=True)


if __name__=='__main__':
    main()
