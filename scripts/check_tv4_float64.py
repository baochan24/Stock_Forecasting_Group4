"""Exercise TV4 CPU float64 with both TV3 models; synthetic data only."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.training.trainer import _read_batch, _run_epoch


def main():
    folder = ROOT / 'logs/audit' / ('tv4_float64_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    paths = [ROOT / p for p in ['backend/training/trainer.py', 'backend/models/lstm_one_step/model.py', 'backend/models/lstm_multi_step/model.py']]
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    global_dtype = torch.get_default_dtype()
    rows = []
    for cls in [LSTMOneStep, LSTMMultiStep]:
        torch.manual_seed(17)
        model = cls()
        x = torch.linspace(-1, 1, 90, dtype=torch.float64).reshape(3, 30, 1)
        y = torch.zeros(3, model.forecast_length, dtype=torch.float64)
        originals = x.clone(), y.clone()
        loader = DataLoader(TensorDataset(x, y), batch_size=2, drop_last=False)
        before = {k: p.clone().detach() for k, p in model.named_parameters()}
        optimizer = torch.optim.Adam(model.parameters(), lr=.001)
        sizes = []
        handle = model.register_forward_pre_hook(lambda module, args: sizes.append(args[0].shape[0]))
        train_loss = _run_epoch(model, loader, nn.MSELoss(), optimizer)
        train_sizes = sizes.copy()
        updated = any(not torch.equal(before[k], p) for k, p in model.named_parameters())
        state = {k: p.clone().detach() for k, p in model.named_parameters()}
        grads = {k: p.grad.clone() for k, p in model.named_parameters()}
        sizes.clear()
        val_loss = _run_epoch(model, loader, nn.MSELoss())
        handle.remove()
        preserved = all(torch.equal(p, state[k]) and torch.equal(p.grad, grads[k]) for k, p in model.named_parameters())
        rejected = False
        try:
            _read_batch((x.float(), y), model=model)
        except TypeError:
            rejected = True
        dtype_ok = all(p.dtype == torch.float64 and p.grad.dtype == torch.float64 for p in model.parameters())
        finite = all(torch.isfinite(p).all() and torch.isfinite(p.grad).all() for p in model.parameters())
        assert math.isfinite(train_loss) and math.isfinite(val_loss) and updated and preserved and rejected and dtype_ok and finite
        assert train_sizes == sizes == [2, 1]
        assert torch.equal(x, originals[0]) and torch.equal(y, originals[1])
        rows.append({'model': cls.__name__, 'X_shape': list(x.shape), 'y_shape': list(y.shape),
                     'X_dtype': str(x.dtype), 'target_dtype': str(y.dtype), 'parameter_dtype': str(next(model.parameters()).dtype),
                     'device': str(next(model.parameters()).device), 'train_loss_synthetic': train_loss, 'validation_loss_synthetic': val_loss,
                     'train_batch_sizes': train_sizes, 'validation_batch_sizes': sizes.copy(), 'weights_updated': updated,
                     'validation_weights_gradients_unchanged': preserved, 'float32_rejected': rejected, 'finite_parameters_gradients': bool(finite)})
    assert torch.get_default_dtype() == global_dtype
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value for name, value in hashes.items())
    summary = {'passed': True, 'scope': 'Synthetic contract probe; no AAPL, no saved checkpoint, no forecasting metric',
               'default_dtype_unchanged': True, 'source_hashes': hashes, 'checks': rows, 'evidence': str(folder / 'summary.json')}
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'passed': True, 'evidence': summary['evidence']}, indent=2))


if __name__ == '__main__':
    main()
