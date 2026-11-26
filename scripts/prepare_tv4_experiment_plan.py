"""Build immutable lookback artifacts and verify the common-date run grid."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import sys
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.windows import _create_windows
from backend.artifacts.scaler import load_scaler
from backend.artifacts.prepared import save_prepared_modes
from backend.audit.tv2_leakage import audit_temporal_windows
from backend.data.validation.validator import compute_sha256
from backend.experiments.runner.aapl_factories import make_aapl_loaders
from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments
from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint
from backend.training.trainer import _run_epoch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reuse', type=Path)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = args.reuse.resolve() if args.reuse else ROOT / 'logs/audit' / f'tv4_item7_{stamp}'
    folder.mkdir(parents=True, exist_ok=bool(args.reuse))
    torch.set_num_threads(1)
    base = load_experiment_config(ROOT / 'experiments/configs/lstm_one_step_baseline.yaml')
    data = base['data']
    snapshot = load_tv1_snapshot(ROOT, data['dataset_version'])
    hashes = snapshot['acceptance']['hashes']
    scaler, manifest = load_scaler(ROOT / 'artifacts/scalers' / data['scaler_id'],
        expected_dataset_version=data['dataset_version'], expected_source_hashes=hashes)
    dates = {}
    configs = []
    for lookback in (10, 30, 60):
        existing = folder / f'one_step_lb{lookback}.yaml'
        if args.reuse and existing.is_file():
            config = load_experiment_config(existing)
            train, val = make_aapl_loaders(config, 42, project_root=ROOT)
            dates[lookback] = [train.dataset.target_dates, val.dataset.target_dates]
            configs.append(str(existing))
            continue
        modes = {h: _create_windows(snapshot['data'], scaler, h, lookback) for h in (1, 5)}
        for result in modes.values():
            audit_temporal_windows(result, snapshot['data'], scaler)
        prepared = save_prepared_modes(modes, ROOT / 'data/prepared', f'tv4_lb{lookback}_{stamp}', data['scaler_id'], hashes)
        config = load_experiment_config(ROOT / 'experiments/configs/lstm_one_step_baseline.yaml')
        config['data'].update(lookback=lookback, common_history=True, prepared_id=prepared.name,
                              prepared_manifest_sha256=compute_sha256(prepared / 'manifest.json'))
        config['runtime'] = {'torch_threads': 1}
        config['experiment_name'] = f'lstm_one_step_lb{lookback}_common60'
        path = folder / f'one_step_lb{lookback}.yaml'
        path.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
        train, val = make_aapl_loaders(config, 42, project_root=ROOT)
        dates[lookback] = [train.dataset.target_dates, val.dataset.target_dates]
        assert train.dataset.X.shape[1:] == (lookback, 1)
        configs.append(str(path))
    assert dates[10] == dates[30] == dates[60]
    multi = load_experiment_config(ROOT / 'experiments/configs/lstm_multi_step_baseline.yaml')
    multi['runtime'] = {'torch_threads': 1}
    path = folder / 'five_step_lb30.yaml'
    path.write_text(yaml.safe_dump(multi, sort_keys=False), encoding='utf-8')
    configs.append(str(path))
    probes = []
    for index, original in enumerate(configs):
        config = load_experiment_config(original)
        config['training']['max_epochs'] = 1
        config['seeds'] = [42]
        config['output'] = {'log_dir': str(folder / 'probe_runs'),
                            'checkpoint_dir': str(ROOT / 'artifacts/checkpoints' / f'tv4_item7_{stamp}')}
        path = folder / f'probe_{index}.yaml'
        path.write_text(yaml.safe_dump(config), encoding='utf-8')
        result, = run_experiments(path)
        _, validation = make_aapl_loaders(config, 42, project_root=ROOT)
        identity = validation.dataset.provenance
        restored, _ = load_lstm_checkpoint(result['checkpoint_path'],
            expected_dataset_version=identity['dataset_version'], expected_source_hashes=identity['source_hashes'],
            expected_scaler_id=identity['scaler_id'], expected_forecast_length=config['data']['forecast_length'],
            expected_lookback=config['data']['lookback'])
        import math
        assert math.isclose(_run_epoch(restored, validation, torch.nn.MSELoss()), result['best_val_loss'], rel_tol=1e-12)
        run = folder / 'probe_runs' / result['run_id']
        import csv
        with (run / 'epoch_logs.csv').open() as stream:
            row, = list(csv.DictReader(stream))
        assert float(row['train_seconds']) > 0 and float(row['validation_seconds']) > 0
        assert len(json.loads(row['val_mse_per_horizon'])) == config['data']['forecast_length']
        meta = json.loads((run / 'metadata.json').read_text())
        assert meta['torch_threads'] == 1 and 'config_yaml' in meta['source_files_sha256']
        probes.append(str(run))
    summary = dict(passed=True, configs=configs, seeds=[42,123,456], planned_runs=12,
                   max_epochs=1200, common_train_samples=len(dates[30][0]),
                   common_val_samples=len(dates[30][1]), probe_runs=probes,
                   scope='artifact audit and one-epoch integration probes, seed42')
    path = folder / 'summary.json'
    path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'evidence': str(path)}))


if __name__ == '__main__':
    main()
