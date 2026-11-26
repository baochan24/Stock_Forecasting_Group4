"""Audit the full CNN train/validation inputs against recorded TV4 sample order."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.experiments.runner.cnn_data import make_cnn_comparison_loaders
from backend.experiments.runner.experiment_runner import load_experiment_config
from backend.models.cnn_one_step import CNNOneStep


def main():
    torch.set_num_threads(1)
    config = load_experiment_config(ROOT / 'logs/audit/tv4_item7_20261125T120957429763Z/one_step_lb30.yaml')
    previous = json.loads((ROOT / 'logs/audit/tv4_item8_20261125T122649342552Z/summary.json').read_text())
    selected = next(r for r in previous['results'] if r['lookback'] == 30 and r['seed'] == 42)
    original = ROOT / 'logs/audit/tv4_item8_20261125T122649342552Z/runs' / selected['run_id'] / 'metadata.json'
    meta = json.loads(original.read_text())
    assert config['data'] == meta['config']['data']
    loaders = make_cnn_comparison_loaders(config, 42, project_root=ROOT)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(42)
        model = CNNOneStep().eval()
    prepared = ROOT / 'data/prepared' / config['data']['prepared_id']
    rows = []
    for split, loader in zip(['train','val'], loaders):
        ds = loader.dataset
        expected_targets = json.loads((prepared / f'f1_{split}_targets.json').read_text())
        with np.load(prepared / f'f1_{split}.npz', allow_pickle=False) as arrays:
            keep = arrays['target_indices'] >= 60
            expected_X, expected_y = arrays['X'][keep], arrays['y'][keep]
        expected_ids = [row['sample_id'] for row, use in zip(expected_targets, keep) if use]
        expected_dates = [tuple(row['target_dates']) for row, use in zip(expected_targets, keep) if use]
        assert list(ds.sample_ids) == expected_ids and list(ds.target_dates) == expected_dates
        assert ds.provenance['source_hashes'] == meta['source_hashes']
        seen = 0
        with torch.inference_mode():
            for x, y, ids in loader:
                count = len(ids)
                assert x.dtype == y.dtype == torch.float64 and x.device.type == 'cpu'
                assert list(ids) == expected_ids[seen:seen+count]
                np.testing.assert_array_equal(x.numpy(), expected_X[seen:seen+count])
                np.testing.assert_array_equal(y.numpy(), expected_y[seen:seen+count])
                output = model(x)
                assert output.shape == y.shape and torch.isfinite(output).all()
                seen += count
        assert seen == len(ds)
        np.testing.assert_array_equal(ds.X.numpy(), expected_X)
        np.testing.assert_array_equal(ds.y.numpy(), expected_y)
        assert all(origin < target[0] for origin, target in zip(ds.origins, ds.target_dates))
        rows.append(dict(split=split, samples=seen, batches=len(loader),
                         final_batch=count, first_origin=ds.origins[0],
                         first_target=ds.target_dates[0][0], last_target=ds.target_dates[-1][-1],
                         ordered_ids_sha256=hashlib.sha256('\n'.join(expected_ids).encode()).hexdigest(),
                         input_shape=list(ds.X.shape), target_shape=list(ds.y.shape)))
        rows[-1]['example'] = dict(sample_id=ds.sample_ids[0], origin=ds.origins[0],
            target_date=ds.target_dates[0][0], last_five_scaled=ds.X[0,-5:,0].tolist(),
            target_scaled=ds.y[0,0].item())
    folder = ROOT / 'logs/audit' / ('tv5_item3_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    path = folder / 'summary.json'
    path.write_text(json.dumps(dict(passed=True, scope='CNN input/forward, initialized model',
        trained=False, results=rows, provenance=loaders[0].dataset.provenance), indent=2))
    print(json.dumps(dict(evidence=str(path))))


if __name__ == '__main__':
    main()
