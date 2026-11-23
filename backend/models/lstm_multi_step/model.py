"""LSTM direct multi-output dự báo đồng thời năm phiên giao dịch."""

import torch

from backend.models.lstm_one_step.model import _LSTMRegressor


class LSTMMultiStep(_LSTMRegressor):
    """LSTM riêng với Linear ra năm giá, không dự báo recursive."""

    def __init__(
        self, input_size: int = 1, hidden_size: int = 32, forecast_length: int = 5
    ):
        if type(forecast_length) is not int or forecast_length != 5:
            raise ValueError("The project multi-step model requires forecast_length=5")
        # Tạo bộ trọng số mới; không tái sử dụng checkpoint một bước.
        super().__init__(input_size, hidden_size, output_size=forecast_length)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Nhận (B, 30, 1), trả (B, 5) trong một lần forward."""
        return super().forward(x)
