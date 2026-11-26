"""LSTM một lớp, dự báo giá chuẩn hóa của phiên kế tiếp."""

import torch
from torch import nn


class _LSTMRegressor(nn.Module):
    """Logic LSTM dùng chung cho hai horizon, không chứa training/scaler."""

    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        super().__init__()
        for name, size in (
            ("input_size", input_size),
            ("hidden_size", hidden_size),
            ("output_size", output_size),
        ):
            if type(size) is not int or size < 1:
                raise ValueError(f"{name} must be a positive integer")
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.forecast_length = output_size
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=1, batch_first=True, dtype=torch.float64)
        self.fc = nn.Linear(hidden_size, output_size, dtype=torch.float64)

    def _validate_input(self, x: torch.Tensor) -> None:
        if not isinstance(x, torch.Tensor):
            raise TypeError("x must be a torch.Tensor")
        if x.ndim != 3 or x.shape[-1] != self.input_size:
            raise ValueError(f"Expected x shape (B, T, {self.input_size})")
        if x.shape[0] == 0 or x.shape[1] == 0:
            raise ValueError("Batch and sequence must not be empty")
        if not x.is_floating_point():
            raise TypeError("x must be a floating-point tensor")
        if x.dtype != self.lstm.weight_ih_l0.dtype:
            raise TypeError("x dtype must match model dtype (default float64)")
        if x.device != self.lstm.weight_ih_l0.device:
            raise ValueError("x device must match model device")
        if not torch.isfinite(x).all():
            raise ValueError("x contains NaN or Inf")

    def _initial_state(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # Mỗi lần forward tạo hai tensor zero mới, không truyền state giữa mẫu.
        shape = (1, x.shape[0], self.hidden_size)
        return x.new_zeros(shape), x.new_zeros(shape)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Dự báo từ tensor (B, T, input_size), trả (B, forecast_length).

        T mặc định do TV2 cấu hình là 30; mạng cũng hỗ trợ thử nghiệm 10/60.
        Giá đầu vào và đầu ra đều ở thang chuẩn hóa.
        """
        self._validate_input(x)
        # LSTM đọc từng time step; Linear dùng biểu diễn của time step cuối.
        sequence, _ = self.lstm(x, self._initial_state(x))
        prediction = self.fc(sequence[:, -1, :])
        if not torch.isfinite(prediction).all():
            raise FloatingPointError("LSTM prediction contains NaN or Inf")
        return prediction


class LSTMOneStep(_LSTMRegressor):
    """LSTM một lớp và Linear ra một giá, đúng interface TV3 mục 5."""

    def __init__(self, input_size: int = 1, hidden_size: int = 32):
        super().__init__(input_size, hidden_size, output_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Nhận (B, 30, 1) theo cấu hình mặc định, trả (B, 1)."""
        return super().forward(x)
