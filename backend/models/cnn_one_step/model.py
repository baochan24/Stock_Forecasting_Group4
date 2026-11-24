from __future__ import annotations

from dataclasses import asdict, dataclass

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
            nn.Conv1d(c.n_features, c.conv1_channels, c.kernel_size, padding=pad),
            nn.ReLU(),
            nn.Conv1d(c.conv1_channels, c.conv2_channels, c.kernel_size, padding=pad),
            nn.ReLU(),
            nn.MaxPool1d(c.pool_size),
        )
        flat_dim = c.conv2_channels * (c.lookback // c.pool_size)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(c.dropout),
            nn.Linear(flat_dim, c.hidden_units),
            nn.ReLU(),
            nn.Linear(c.hidden_units, c.output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3 or x.shape[1:] != (self.config.lookback, self.config.n_features):
            raise ValueError(
                f"Cần input (batch, {self.config.lookback}, {self.config.n_features}), "
                f"nhận {tuple(x.shape)}."
            )
        # (B, L, F) -> (B, F, L) cho Conv1d
        return self.head(self.features(x.transpose(1, 2)))

    # --- tiện ích phục vụ ghi tham số/ngân sách trong báo cáo ---
    def count_parameters(self, trainable_only: bool = True) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad or not trainable_only)

    def get_config(self) -> dict:
        """Dict thuần để ghi vào config/checkpoint (tái tạo model khi nạp)."""
        return asdict(self.config)

    @classmethod
    def from_config(cls, cfg: dict) -> "CNNOneStep":
        return cls(CNNOneStepConfig(**cfg))