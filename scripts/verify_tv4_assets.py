"""Verify a relative-path inventory against any relocated coursework root."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--models', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / 'reports/audits/TV4_Run_Assets.json').read_text(encoding='utf-8'))
    failures = []
    for name, expected in manifest['files'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f'Path outside workspace: {name}')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(name)
    if not failures and args.models:
        import math
        import numpy as np
        import torch
        sys.path.insert(0, str(root))
        from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint
        torch.set_num_threads(1)
        for run in manifest['runs']:
            meta = json.loads((root / run['metadata']).read_text(encoding='utf-8'))
            data = meta['config']['data']
            model, _ = load_lstm_checkpoint(root / run['checkpoint'],
                expected_dataset_version=data['dataset_version'], expected_source_hashes=meta['source_hashes'],
                expected_scaler_id=data['scaler_id'], expected_forecast_length=data['forecast_length'],
                expected_lookback=data['lookback'])
            model_module = sys.modules[type(model).__module__]
            assert Path(model_module.__file__).resolve().is_relative_to(root)
            with np.load(root / 'data/prepared' / data['prepared_id'] / f"f{data['forecast_length']}_val.npz") as arrays:
                mask = arrays['target_indices'] >= 60 if data.get('common_history') else np.ones(len(arrays['X']), dtype=bool)
                X, y = arrays['X'][mask], arrays['y'][mask]
            with torch.inference_mode():
                predicted = torch.cat([model(torch.from_numpy(X[i:i+32])) for i in range(0, len(X), 32)]).numpy()
            assert math.isclose(float(np.mean((predicted-y)**2)), meta['best_val_loss'], rel_tol=1e-12)
    print(json.dumps(dict(passed=not failures, files=len(manifest['files']), failures=failures,
                         models_verified=len(manifest['runs']) if args.models and not failures else 0), indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
