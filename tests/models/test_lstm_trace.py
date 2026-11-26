"""Kiểm tra trace số học, tính chỉ đọc và khả năng tuần tự hóa JSON."""

import json
from unittest.mock import patch

import pytest
import torch

from backend.model_trace import trace_lstm
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.models.lstm_one_step import LSTMOneStep


@pytest.fixture(params=[LSTMOneStep, LSTMMultiStep])
def model(request):
    torch.manual_seed(42)
    return request.param().eval()


def test_trace_matches_forward_and_states(model):
    x = torch.randn(1, 30, 1, dtype=torch.float64)
    trace = trace_lstm(model, x)
    assert trace["verification"]["passed"] is True
    assert len(trace["steps"]) == 30
    assert trace["output_shape"] == [1, model.forecast_length]
    assert trace["initial_hidden"] == trace["initial_cell"] == [0.0] * 32
    assert trace["linear_input"] == trace["steps"][-1]["hidden_state"]
    torch.testing.assert_close(torch.tensor(trace["prediction_scaled"], dtype=torch.float64), model(x)[0])
    for step in trace["steps"]:
        for gate in ("input_gate", "forget_gate", "output_gate"):
            assert len(step[gate]) == 32
            assert all(0 <= v <= 1 for v in step[gate])
        assert all(-1 <= v <= 1 for v in step["candidate_state"])
    json.dumps(trace, allow_nan=False)


def test_trace_read_only(model):
    weights = {k: v.clone() for k, v in model.state_dict().items()}
    x = torch.randn(1, 30, 1, requires_grad=True, dtype=torch.float64)
    trace_lstm(model, x)
    assert not model.training
    assert x.grad is None
    for key, value in model.state_dict().items():
        assert torch.equal(value, weights[key])
    assert all(p.grad is None for p in model.parameters())


def test_trace_rejects_training_mode(model):
    model.train()
    with pytest.raises(ValueError, match="eval"):
        trace_lstm(model, torch.randn(1, 30, 1, dtype=torch.float64))


def test_trace_rejects_multiple_windows(model):
    with pytest.raises(ValueError, match="one representative"):
        trace_lstm(model, torch.randn(2, 30, 1, dtype=torch.float64))


def test_trace_fails_on_forward_mismatch(model):
    x = torch.randn(1, 30, 1, dtype=torch.float64)
    with patch.object(model, "forward", return_value=model(x) + 1):
        with pytest.raises(RuntimeError, match="Trace mismatch"):
            trace_lstm(model, x)


def test_trace_after_optimizer_step(model):
    x = torch.randn(1, 30, 1, dtype=torch.float64)
    model.train()
    optimizer = torch.optim.Adam(model.parameters())
    optimizer.zero_grad()
    model(x).square().mean().backward()
    optimizer.step()
    model.eval()
    assert trace_lstm(model, x)["verification"]["passed"]
