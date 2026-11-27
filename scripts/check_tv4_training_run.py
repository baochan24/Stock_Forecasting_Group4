"""Exercise the run lifecycle on the first 33 training and validation windows."""
import csv
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import torch
from torch.utils.data import DataLoader, Subset
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.experiments.runner.aapl_factories import make_aapl_loaders, make_aapl_model
from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', action='store_true')
    args = parser.parse_args()
    folder = ROOT / 'logs/audit' / (('tv4_item5_' if args.checkpoint else 'tv4_item4_') + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    config = load_experiment_config(ROOT / 'experiments/configs/lstm_one_step_baseline.yaml')
    config['experiment_name'] = 'item5_first33_reload' if args.checkpoint else 'item4_first33_ram'
    config['seeds'] = [config['seeds'][0]]
    config['acceptance_probe'] = {'selection': 'first 33 windows of each split',
                                  'checkpoint': 'disk reload' if args.checkpoint else 'memory'}
    config['output']['log_dir'] = str(folder / 'runs')
    config['output']['checkpoint_dir'] = str(ROOT / 'artifacts/checkpoints' / folder.name)
    config_path = folder / 'config.yaml'
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')

    torch.set_num_threads(1)
    train, validation = make_aapl_loaders(config, config['seeds'][0], project_root=ROOT)
    splits = []
    loaders = []
    for split, source in [('train', train), ('validation', validation)]:
        subset = Subset(source.dataset, range(33))
        subset.provenance = source.dataset.provenance
        loaders.append(DataLoader(subset, batch_size=source.batch_size, shuffle=False))
        dates = source.dataset.target_dates
        splits.append({'split': split, 'samples': len(subset), 'first_target': dates[0][0], 'last_target': dates[32][0]})

    models = []
    def model_factory(settings):
        model = make_aapl_model(settings)
        models.append(model)
        return model

    result, = run_experiments(config_path, model_factory, lambda settings, seed: loaders, persist_checkpoint=args.checkpoint)
    run_dir = folder / 'runs' / result['run_id']
    metadata = json.loads((run_dir / 'metadata.json').read_text(encoding='utf-8'))
    with (run_dir / 'epoch_logs.csv').open(encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    assert metadata['status'] == 'completed'
    assert len(rows) == metadata['epochs_completed'] == len(result['epoch_logs'])
    assert metadata['source_hashes'] == train.dataset.provenance['source_hashes']
    best = min(rows, key=lambda row: float(row['val_loss']))
    assert int(best['epoch']) == result['best_epoch']
    if result['early_stopped']:
        assert len(rows) - result['best_epoch'] == config['training']['early_stopping']['patience']
    else:
        assert len(rows) == config['training']['max_epochs']
    with torch.inference_mode():
        errors = [(models[0](x) - y).square().flatten() for x, y, ids in loaders[1]]
        restored_loss = torch.cat(errors).mean().item()
    assert math.isclose(restored_loss, float(best['val_loss']), rel_tol=1e-12, abs_tol=1e-14)
    assert math.isclose(restored_loss, metadata['best_val_loss'], rel_tol=1e-12, abs_tol=1e-14)
    if args.checkpoint:
        from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint
        identity = train.dataset.provenance
        loaded, manifest = load_lstm_checkpoint(result['checkpoint_path'],
            expected_dataset_version=identity['dataset_version'], expected_source_hashes=identity['source_hashes'],
            expected_scaler_id=identity['scaler_id'], expected_forecast_length=1)
        assert loaded is not models[0] and manifest['metadata']['best_epoch'] == result['best_epoch']
        with torch.inference_mode():
            for x, y, ids in loaders[1]:
                torch.testing.assert_close(loaded(x), models[0](x), rtol=0, atol=0)
    summary = {'passed': True, 'scope': 'one-step AAPL subset, disk reload' if args.checkpoint else 'one-step AAPL subset, best in RAM', 'splits': splits,
               'run_id': result['run_id'], 'run_dir': run_dir.relative_to(ROOT).as_posix(),
               'best_epoch': result['best_epoch'], 'epochs': len(rows), 'best_val_loss': result['best_val_loss'],
               'restored_val_mse': restored_loss, 'early_stopped': result['early_stopped'],
               'patience': config['training']['early_stopping']['patience'], 'checkpoint_path': result['checkpoint_path'],
               'reload_verified': args.checkpoint}
    evidence = folder / 'summary.json'
    evidence.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'evidence': str(evidence)}))


if __name__ == '__main__':
    main()
