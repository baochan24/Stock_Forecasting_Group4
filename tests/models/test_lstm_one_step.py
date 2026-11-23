"""Kiểm thử kiến trúc một bước của TV3 trên CPU, dữ liệu tổng hợp."""

import pytest
import torch

from backend.models.lstm_one_step import LSTMOneStep


@pytest.mark.parametrize("batch_size", [1, 4, 32, 128])
def test_forward_output_shape_and_finite(batch_size):
    model = LSTMOneStep()
    prediction = model(torch.randn(batch_size, 30, 1, dtype=torch.float64))
    assert prediction.shape == (batch_size, 1)
    assert torch.isfinite(prediction).all()


def test_parameter_count():
    model = LSTMOneStep()
    assert sum(p.numel() for p in model.parameters()) == 4513


@pytest.mark.parametrize("shape", [(30, 1), (2, 30, 2), (0, 30, 1), (2, 0, 1)])
def test_invalid_shape(shape):
    with pytest.raises(ValueError):
        LSTMOneStep()(torch.zeros(shape, dtype=torch.float64))


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -float("inf")])
def test_invalid_input_value(bad_value):
    x = torch.zeros(1, 30, 1, dtype=torch.float64)
    x[0, 0, 0] = bad_value
    with pytest.raises(ValueError, match="NaN or Inf"):
        LSTMOneStep()(x)


@pytest.mark.parametrize("dtype", [torch.int64, torch.float32])
def test_invalid_dtype(dtype):
    with pytest.raises(TypeError):
        LSTMOneStep()(torch.zeros(1, 30, 1, dtype=dtype))


@pytest.mark.parametrize("lookback", [10, 30, 60])
def test_supported_lookback(lookback):
    assert LSTMOneStep()(torch.randn(3, lookback, 1, dtype=torch.float64)).shape == (3, 1)
