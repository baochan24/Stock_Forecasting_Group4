"""Kiểm thử dự báo đồng thời năm phiên của TV3."""

import pytest
import torch

from backend.models.lstm_multi_step import LSTMMultiStep


@pytest.mark.parametrize("batch_size", [1, 4, 32, 128])
def test_forward_output_shape_and_finite(batch_size):
    prediction = LSTMMultiStep()(torch.randn(batch_size, 30, 1))
    assert prediction.shape == (batch_size, 5)
    assert torch.isfinite(prediction).all()


def test_parameter_count():
    assert sum(p.numel() for p in LSTMMultiStep().parameters()) == 4645


def test_direct_multi_output():
    model = LSTMMultiStep()
    calls = []
    hook = model.lstm.register_forward_hook(lambda *args: calls.append(1))
    try:
        output = model(torch.randn(2, 30, 1))
    finally:
        hook.remove()
    assert calls == [1]
    assert output.shape == (2, 5)
    assert model.fc.out_features == 5


@pytest.mark.parametrize("horizon", [0, 1, 4, 6, 5.0])
def test_invalid_forecast_length(horizon):
    with pytest.raises(ValueError):
        LSTMMultiStep(forecast_length=horizon)
