"""Hợp đồng chung giữa model TV3 và training/inference của nhóm."""

import io

import pytest
import torch
from torch import nn

from backend.models.lstm_multi_step import LSTMMultiStep
from backend.models.lstm_one_step import LSTMOneStep


@pytest.mark.parametrize("model_type", [LSTMOneStep, LSTMMultiStep])
def test_default_parameters_are_float64_without_global_dtype_change(model_type):
    before = torch.get_default_dtype()
    instance = model_type()
    assert all(p.dtype == torch.float64 for p in instance.parameters())
    assert torch.get_default_dtype() == before


@pytest.fixture(params=[LSTMOneStep, LSTMMultiStep])
def model(request):
    # Seed chỉ dùng cho unit test, không phải seed thực nghiệm chính thức.
    torch.manual_seed(42)
    return request.param()


def test_gradient_flow(model):
    x = torch.randn(4, 30, 1, requires_grad=True, dtype=torch.float64)
    model(x).sum().backward()
    for p in model.parameters():
        assert p.grad is not None
        assert torch.isfinite(p.grad).all()
        assert torch.count_nonzero(p.grad) > 0
    assert x.grad is not None and torch.isfinite(x.grad).all()


def test_independent_windows(model):
    model.eval()
    a = torch.randn(1, 30, 1, dtype=torch.float64)
    b = torch.randn(1, 30, 1, dtype=torch.float64)
    with torch.no_grad():
        expected = model(a)
        model(b)
        torch.testing.assert_close(model(a), expected)
        torch.testing.assert_close(model(torch.cat([a, b]))[:1], expected)
        torch.testing.assert_close(model(torch.cat([b, a]))[1:], expected)


def test_zero_initial_state(model):
    captured = []
    hook = model.lstm.register_forward_pre_hook(
        lambda m, args: captured.append(args[1])
    )
    try:
        model(torch.randn(2, 30, 1, dtype=torch.float64))
        model(torch.randn(2, 30, 1, dtype=torch.float64))
    finally:
        hook.remove()
    for h, c in captured:
        assert h.shape == c.shape == (1, 2, 32)
        assert torch.count_nonzero(h) == torch.count_nonzero(c) == 0
        assert h.data_ptr() != c.data_ptr()
    assert captured[0][0].data_ptr() != captured[1][0].data_ptr()


def test_optimizer_step_smoke(model):
    # Chỉ kiểm tra khả năng backward/Adam/MSE; không thay training loop TV4.
    x = torch.randn(8, 30, 1, dtype=torch.float64)
    y = torch.randn(8, model.forecast_length, dtype=torch.float64)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    before = [p.detach().clone() for p in model.parameters()]
    optimizer.zero_grad()
    prediction = model(x)
    assert prediction.shape == y.shape
    loss = nn.MSELoss()(prediction, y)
    assert torch.isfinite(loss)
    loss.backward()
    optimizer.step()
    assert any(not torch.equal(a, b) for a, b in zip(before, model.parameters()))


def test_state_dict_roundtrip(model):
    x = torch.randn(2, 30, 1, dtype=torch.float64)
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    buffer.seek(0)
    restored = type(model)()
    restored.load_state_dict(torch.load(buffer, map_location="cpu", weights_only=True))
    model.eval()
    restored.eval()
    with torch.no_grad():
        torch.testing.assert_close(model(x), restored(x))


def test_nonfinite_prediction_is_rejected(model):
    with torch.no_grad():
        model.fc.bias.fill_(float("nan"))
    with pytest.raises(FloatingPointError):
        model(torch.zeros(1, 30, 1, dtype=torch.float64))


def test_custom_hidden_size(model):
    resized = type(model)(hidden_size=16)
    assert resized(torch.randn(3, 30, 1, dtype=torch.float64)).shape == (3, model.forecast_length)


def test_tv2_sample_format(model, tv2_source):
    # Official TV2 module output, synthetic dates/prices (not full-calendar data).
    from backend.data.preparation.windows import create_one_step_windows,create_five_step_windows
    from backend.data.preparation.tensors import make_lstm_training_batch
    data,scaler = tv2_source
    create = create_one_step_windows if model.forecast_length == 1 else create_five_step_windows
    batch = create(data,scaler)["splits"]["val"]
    packed = make_lstm_training_batch(batch,scaler,dataset_version="fixture",forecast_length=model.forecast_length)
    x,y = packed["X"],packed["y"]
    prediction = model(x)
    assert prediction.shape == y.shape
    assert prediction.dtype == y.dtype == torch.float64
