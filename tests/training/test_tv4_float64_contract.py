"""TV4 item2: real TV3 models with synthetic tensors; no AAPL/checkpoint claim."""
import numpy as np
import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.training import trainer


@pytest.fixture(params=[LSTMOneStep, LSTMMultiStep], ids=['one_step', 'five_step'])
def model(request):
    torch.manual_seed(17)
    return request.param()


def batch(model, length=30):
    x = torch.linspace(-1, 1, 3*length, dtype=torch.float64).reshape(3, length, 1)
    y = torch.zeros(3, model.forecast_length, dtype=torch.float64)
    return x, y


def test_preserves_numpy_values_and_global_dtype(model):
    x, y = batch(model)
    before = torch.get_default_dtype()
    actual_x, actual_y = trainer._read_batch({'inputs': x.numpy(), 'targets': y.numpy()}, model=model)
    assert actual_x.dtype == actual_y.dtype == torch.float64
    assert actual_x.device.type == actual_y.device.type == 'cpu'
    np.testing.assert_array_equal(actual_x.numpy(), x.numpy())
    np.testing.assert_array_equal(actual_y.numpy(), y.numpy())
    assert torch.get_default_dtype() == before


def test_train_and_validation_keep_float64_and_final_batch(model):
    x, y = batch(model)
    originals = x.clone(), y.clone()
    loader = DataLoader(TensorDataset(x, y), batch_size=2, drop_last=False)
    sizes = []
    handle = model.register_forward_pre_hook(lambda module, args: sizes.append(args[0].shape[0]))
    before = {n: p.detach().clone() for n, p in model.named_parameters()}
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    loss = trainer._run_epoch(model, loader, nn.MSELoss(), optimizer)
    assert np.isfinite(loss) and sizes == [2, 1]
    assert any(not torch.equal(before[n], p) for n, p in model.named_parameters())
    assert all(p.dtype == torch.float64 and torch.isfinite(p).all() for p in model.parameters())
    assert all(p.grad is not None and p.grad.dtype == torch.float64 and torch.isfinite(p.grad).all() for p in model.parameters())
    assert all(state['exp_avg'].dtype == state['exp_avg_sq'].dtype == torch.float64 for state in optimizer.state.values())
    snapshot = {n: p.detach().clone() for n, p in model.named_parameters()}
    gradients = {n: p.grad.clone() for n, p in model.named_parameters()}
    sizes.clear()
    result = trainer._run_epoch(model, loader, nn.MSELoss())
    assert np.isfinite(result) and sizes == [2, 1] and not model.training
    assert all(torch.equal(p, snapshot[n]) and torch.equal(p.grad, gradients[n]) for n, p in model.named_parameters())
    assert torch.equal(x, originals[0]) and torch.equal(y, originals[1])
    handle.remove()


@pytest.mark.parametrize('field', ['inputs', 'targets'])
def test_rejects_float32_without_silent_conversion(model, field):
    x, y = batch(model)
    values = {'inputs': x, 'targets': y}
    values[field] = values[field].float()
    with pytest.raises(TypeError, match='no implicit cast'):
        trainer._read_batch(values, model=model)


def test_rejects_downcast_lstm_model(model):
    with pytest.raises(TypeError, match='float64 parameters'):
        trainer._read_batch(tuple(t.float() for t in batch(model)), model=model.float())


@pytest.mark.parametrize('kind', ['horizon', 'feature', 'length', 'rank', 'empty', 'count', 'integer', 'nonfinite', 'device'])
def test_rejects_invalid_lstm_batch(model, kind):
    x, y = batch(model)
    expected = ValueError
    if kind == 'horizon': y = y.repeat(1, 5) if model.forecast_length == 1 else y[:, :1]
    if kind == 'feature': x = x.repeat(1, 1, 2)
    if kind == 'length': x = x[:, :29]
    if kind == 'rank': x = x.squeeze(-1)
    if kind == 'empty': x, y = x[:0], y[:0]
    if kind == 'count': y = y[:1]
    if kind == 'integer': y, expected = y.long(), TypeError
    if kind == 'nonfinite': y[0, 0] = float('nan')
    if kind == 'device': x = x.to('meta')
    with pytest.raises(expected):
        trainer._read_batch((x, y), model=model)


@pytest.mark.parametrize('length', [10, 60])
def test_accepts_planned_lookback_shapes_without_running_experiments(model, length):
    x, y = trainer._read_batch(batch(model, length), model=model)
    assert x.shape == (3, length, 1) and y.shape == (3, model.forecast_length)


def test_rejects_non_cpu_model_without_migration(model):
    model.to('meta')
    with pytest.raises(ValueError, match='CPU model'):
        trainer._read_batch(batch(model), model=model)
    assert next(model.parameters()).device.type == 'meta'


def test_real_train_model_with_checkpoint_explicitly_mocked(model, monkeypatch, tmp_path):
    x, y = batch(model)
    saved = []
    def saver(model, epoch, loss):
        saved.append(epoch)
        return tmp_path / 'synthetic_checkpoint'
    loader = DataLoader(TensorDataset(x, y), batch_size=2)
    config = {'training': {'optimizer': 'adam', 'loss_function': 'mse', 'learning_rate': .001, 'max_epochs': 1,
                           'early_stopping': {'patience': 1, 'monitor': 'val_loss', 'mode': 'min'}}}
    result = trainer.train_model(model, loader, loader, config, None, 'synthetic_dtype_probe', checkpoint_saver=saver)
    assert saved == [1] and result['best_epoch'] == 1
    assert all(p.dtype == torch.float64 for p in model.parameters())
