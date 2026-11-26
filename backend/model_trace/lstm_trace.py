"""Trace tính từ chính trọng số LSTM, có đối chiếu số học trước khi trả."""

import torch
from torch.nn import functional as F

from backend.models.lstm_multi_step import LSTMMultiStep
from backend.models.lstm_one_step import LSTMOneStep

RTOL = 1e-10  # Project float64 model default.
ATOL = 1e-12


@torch.no_grad()
def trace_lstm(model: LSTMOneStep | LSTMMultiStep, x: torch.Tensor) -> dict:
    """Truy vết một cửa sổ chuẩn hóa bằng model thực tế được truyền vào.

    Args:
        model: LSTM TV3 đã được nạp trọng số và chuyển eval mode.
        x: Tensor (1, T, input_size), không nhận target.

    Returns:
        Dict JSON-compatible chứa các gate tái tính, h/c mỗi bước và dự báo.
        Chỉ trả khi state và output khớp phép tính nn.LSTM/forward chính.
        Schema nội bộ đề xuất, chưa phải API chính thức của nhóm.

    Raises:
        ValueError: Input không đúng hoặc model chưa ở eval mode.
        RuntimeError: Đối chiếu số học không đạt.
    """
    if not isinstance(model, (LSTMOneStep, LSTMMultiStep)):
        raise TypeError("Expected an LSTM model from TV3")
    if model.training or model.lstm.training or model.fc.training:
        raise ValueError("Call model.eval() before tracing")
    model._validate_input(x)
    if x.shape[0] != 1:
        raise ValueError("Trace requires exactly one representative window")
    rtol, atol = (RTOL, ATOL) if x.dtype == torch.float64 else (1e-5, 1e-6)
    layer = model.lstm
    initial_h, initial_c = model._initial_state(x)
    h, c = initial_h[0], initial_c[0]
    ref_h, ref_c = initial_h, initial_c
    sequence, (final_h, final_c) = layer(x, (initial_h, initial_c))
    prediction = model(x)
    steps = []
    h_values = []
    max_hidden_error = 0.0
    max_cell_error = 0.0

    def compare(actual: torch.Tensor, expected: torch.Tensor) -> float:
        if not torch.isfinite(actual).all() or not torch.isfinite(expected).all():
            raise RuntimeError("Trace contains non-finite values")
        if not torch.allclose(actual, expected, rtol=rtol, atol=atol):
            raise RuntimeError("Trace mismatch: not verified against the model")
        return float((actual - expected).abs().max().item())

    # PyTorch lưu trọng số cổng theo thứ tự i, f, g, o (hai bias riêng).
    for index in range(x.shape[1]):
        xt = x[:, index, :]
        gates = F.linear(xt, layer.weight_ih_l0, layer.bias_ih_l0)
        gates = gates + F.linear(h, layer.weight_hh_l0, layer.bias_hh_l0)
        i, f, g, o = gates.chunk(4, dim=-1)
        i, f, g, o = i.sigmoid(), f.sigmoid(), g.tanh(), o.sigmoid()
        c = f * c + i * g
        h = o * c.tanh()
        # So sánh cả cell state từng bước với chính nn.LSTM, không chỉ output.
        _, (ref_h, ref_c) = layer(xt.unsqueeze(1), (ref_h, ref_c))
        max_hidden_error = max(max_hidden_error, compare(h, ref_h[0]))
        max_cell_error = max(max_cell_error, compare(c, ref_c[0]))
        h_values.append(h)
        steps.append(
            {
                "time_step": index + 1,
                "input_gate": i[0].tolist(),
                "forget_gate": f[0].tolist(),
                "candidate_state": g[0].tolist(),
                "output_gate": o[0].tolist(),
                "hidden_state": h[0].tolist(),
                "cell_state": c[0].tolist(),
            }
        )

    max_hidden_error = max(
        max_hidden_error,
        compare(torch.stack(h_values, dim=1), sequence),
        compare(h, final_h[0]),
    )
    max_cell_error = max(max_cell_error, compare(c, final_c[0]))
    output_error = compare(model.fc(h), prediction)
    return {
        "trace_type": "reconstructed_and_verified",
        "input_shape": list(x.shape),
        "input_scaled": x[0].tolist(),
        "output_shape": list(prediction.shape),
        "prediction_scaled": prediction[0].tolist(),
        "initial_hidden": initial_h[0, 0].tolist(),
        "initial_cell": initial_c[0, 0].tolist(),
        "steps": steps,
        "linear_input": h[0].tolist(),
        "verification": {
            "passed": True,
            "rtol": rtol,
            "atol": atol,
            "max_hidden_abs_error": max_hidden_error,
            "max_cell_abs_error": max_cell_error,
            "max_prediction_abs_error": output_error,
        },
    }
