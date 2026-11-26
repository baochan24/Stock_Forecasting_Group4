from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import torch
from torch import nn


@dataclass(frozen=True)
class CNNOneStepConfig:
    lookback: int = 30          
    n_features: int = 1         
    conv1_channels: int = 16
    conv2_channels: int = 32
    kernel_size: int = 3       
    pool_size: int = 2
    hidden_units: int = 32
    dropout: float = 0.1
    output_size: int = 1      

    def validate(self) -> None:
        for name in ('lookback', 'n_features', 'conv1_channels', 'conv2_channels',
                     'kernel_size', 'pool_size', 'hidden_units', 'output_size'):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if (self.lookback, self.n_features, self.output_size) != (30, 1, 1):
            raise ValueError("CNN one-step requires lookback 30, one feature and one output")
        if type(self.dropout) not in (int, float) or not math.isfinite(self.dropout):
            raise ValueError("dropout must be finite numeric")
        if self.kernel_size % 2 == 0:
            raise ValueError("kernel_size phải là số lẻ.")
        if self.lookback < self.pool_size:
            raise ValueError("lookback phải >= pool_size.")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout phải trong [0, 1).")


class CNNOneStep(nn.Module):
    """Conv1D x2 -> MaxPool -> Flatten -> MLP nhỏ -> 1 giá trị."""

    def __init__(self, config: CNNOneStepConfig | None = None) -> None:
        super().__init__()
        self.config = config or CNNOneStepConfig()
        c = self.config
        c.validate()
        pad = c.kernel_size // 2
        self.features = nn.Sequential(
            nn.Conv1d(c.n_features, c.conv1_channels, c.kernel_size, padding=pad, dtype=torch.float64),
            nn.ReLU(),
            nn.Conv1d(c.conv1_channels, c.conv2_channels, c.kernel_size, padding=pad, dtype=torch.float64),
            nn.ReLU(),
            nn.MaxPool1d(c.pool_size),
        )
        flat_dim = c.conv2_channels * (c.lookback // c.pool_size)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(c.dropout),
            nn.Linear(flat_dim, c.hidden_units, dtype=torch.float64),
            nn.ReLU(),
            nn.Linear(c.hidden_units, c.output_size, dtype=torch.float64),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if not isinstance(x, torch.Tensor):
            raise TypeError("CNN input must be a tensor")
        if x.device.type != 'cpu' or next(self.parameters()).device.type != 'cpu':
            raise ValueError("CNN requires CPU")
        if x.dtype != torch.float64 or any(p.dtype != torch.float64 for p in self.parameters()):
            raise TypeError("CNN requires float64 input and parameters")
        if x.ndim != 3 or x.shape[1:] != (self.config.lookback, self.config.n_features):
            raise ValueError(
                f"Cần input (batch, {self.config.lookback}, {self.config.n_features}), "
                f"nhận {tuple(x.shape)}."
            )
        # (B, L, F) -> (B, F, L) cho Conv1d
        if x.shape[0] == 0 or not torch.isfinite(x).all():
            raise ValueError("CNN input must be nonempty and finite")
        prediction = self.head(self.features(x.transpose(1, 2)))
        if not torch.isfinite(prediction).all():
            raise FloatingPointError("CNN prediction contains NaN or Inf")
        return prediction

    # --- tiện ích phục vụ ghi tham số/ngân sách trong báo cáo ---
    def count_parameters(self, trainable_only: bool = True) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad or not trainable_only)

    def get_config(self) -> dict:
        """Dict thuần để ghi vào config/checkpoint (tái tạo model khi nạp)."""
        return asdict(self.config)

    @classmethod
    def from_config(cls, cfg: dict) -> "CNNOneStep":
        return cls(CNNOneStepConfig(**cfg))
