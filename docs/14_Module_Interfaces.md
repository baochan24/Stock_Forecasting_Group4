# Module Interfaces — Hợp đồng code giữa các module

Phiên bản: 1.0 — 13/11/2026
Trạng thái: bản đặc tả trước triển khai. Function signatures là điểm khởi đầu, có thể điều chỉnh khi triển khai nhưng phải thống nhất nhóm và ghi Decision Log.

Tài liệu này định nghĩa **hàm/class chính mà mỗi module phải export**, để 6 thành viên code song song mà không lệch interface.

---

## 1. backend/data/acquisition

**Chủ sở hữu: TV1**

```python
def download_aapl_data(
    start_date: str,       # "2015-01-01"
    end_date: str,         # "2025-12-31"
    save_dir: str          # đường dẫn tới data/raw/
) -> dict:
    """
    Tải dữ liệu AAPL từ Yahoo Finance và lưu snapshot.

    Returns:
        {
            "file_path": str,          # đường dẫn file CSV đã lưu
            "num_rows": int,           # số dòng dữ liệu
            "date_range": (str, str),  # (ngày đầu, ngày cuối) thực tế
            "hash": str,              # SHA256 của file
            "download_timestamp": str  # ISO 8601
        }
    """
```

**Output CSV format:**

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `date` | str (YYYY-MM-DD) | Ngày phiên giao dịch |
| `ticker` | str | "AAPL" |
| `adjusted_close` | float | Giá đóng cửa đã điều chỉnh, USD |

---

## 2. backend/data/validation

**Chủ sở hữu: TV1**

```python
def validate_dataset(
    raw_file_path: str
) -> dict:
    """
    Kiểm tra dữ liệu: ngày trùng, ngày thiếu, giá trị bất thường.

    Returns:
        {
            "is_valid": bool,
            "validated_file_path": str,      # đường dẫn data/validated/
            "num_rows": int,
            "issues": [                      # danh sách vấn đề phát hiện
                {"type": str, "description": str, "action": str}
            ],
            "date_range": (str, str),
            "hash": str
        }
    """
```

---

## 3. backend/data/preparation

**Chủ sở hữu: TV2**

```python
def split_data(
    validated_file_path: str
) -> dict:
    """
    Chia dữ liệu theo thời gian.

    Returns:
        {
            "train": {"dates": List[str], "prices": np.ndarray},  # 2015-2022
            "val":   {"dates": List[str], "prices": np.ndarray},  # 2023
            "test":  {"dates": List[str], "prices": np.ndarray},  # 2024-2025
        }
    """


def fit_scaler(
    train_prices: np.ndarray
) -> StandardScaler:
    """Fit StandardScaler trên giá train. Gọi MỘT LẦN."""


def create_windows(
    dates: List[str],
    prices: np.ndarray,
    scaler: StandardScaler,
    lookback: int = 30,
    forecast_length: int = 1,     # 1 hoặc 5
    split_name: str = "train"
) -> dict:
    """
    Tạo cửa sổ input-target.

    Returns:
        {
            "samples": [
                {
                    "sample_id": str,
                    "forecast_origin": str,          # ngày cuối input
                    "input_dates": List[str],         # lookback ngày
                    "input_values": np.ndarray,       # giá gốc
                    "input_scaled": np.ndarray,       # giá đã chuẩn hóa
                    "target_dates": List[str],        # forecast_length ngày
                    "target_values": np.ndarray,      # giá gốc
                    "target_scaled": np.ndarray,      # giá đã chuẩn hóa
                    "split": str                      # "train"/"val"/"test"
                }
            ],
            "num_samples": int,
            "lookback": lookback,
            "forecast_length": forecast_length
        }
    """
```

**Tensor cho PyTorch (TV2 hoặc TV4 chuẩn bị):**

```python
# Input:  torch.Tensor shape (B, lookback, 1) — float32
# Target: torch.Tensor shape (B, forecast_length) — float32
```

---

## 4. backend/data/transforms

**Chủ sở hữu: TV2**

```python
def scale(
    values: np.ndarray,
    scaler: StandardScaler
) -> np.ndarray:
    """Chuẩn hóa. Không fit lại scaler."""


def inverse_scale(
    scaled_values: np.ndarray,
    scaler: StandardScaler
) -> np.ndarray:
    """Khôi phục giá gốc từ giá đã chuẩn hóa."""
```

---

## 5. backend/models/lstm_one_step

**Chủ sở hữu: TV3**

```python
import torch.nn as nn

class LSTMOneStep(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 32):
        """LSTM 1 lớp, Linear ra 1."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: shape (B, 30, 1)
        Returns:
            shape (B, 1)
        """
```

---

## 6. backend/models/lstm_multi_step

**Chủ sở hữu: TV3**

```python
class LSTMMultiStep(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 32, forecast_length: int = 5):
        """LSTM 1 lớp, Linear ra 5."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: shape (B, 30, 1)
        Returns:
            shape (B, 5)
        """
```

---

## 7. backend/models/cnn_one_step

**Chủ sở hữu: TV5**

```python
class CNNOneStep(nn.Module):
    def __init__(self, lookback: int = 30):
        """Kiến trúc CNN 1D cụ thể — cần đặc tả trước triển khai."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: shape (B, 1, 30) hoặc (B, 30, 1) — chốt khi thiết kế CNN
        Returns:
            shape (B, 1)
        """
```

> **Ghi chú:** Kiến trúc CNN chưa chốt (xem `10_Open_Decisions.md`). TV5 đề xuất kiến trúc nhỏ, ghi số tham số, thống nhất nhóm trước khi code.

---

## 8. backend/baselines

**Chủ sở hữu: TV6**

```python
def persistence_forecast(
    last_price: float,
    forecast_length: int = 1
) -> np.ndarray:
    """
    Dự báo bằng giá gần nhất.

    Args:
        last_price: giá gốc cuối cửa sổ input (USD, chưa chuẩn hóa)
        forecast_length: 1 hoặc 5

    Returns:
        np.ndarray shape (forecast_length,) — giá USD
        Ví dụ: forecast_length=5 → [last_price] * 5
    """
```

---

## 9. backend/training

**Chủ sở hữu: TV4**

```python
def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    config: dict,                    # xem 15_Experiment_Config_Schema.md
    checkpoint_dir: str,
    run_id: str
) -> dict:
    """
    Training loop dùng chung cho LSTM và CNN.

    Returns:
        {
            "best_epoch": int,
            "best_val_loss": float,
            "checkpoint_path": str,        # đường dẫn checkpoint tốt nhất
            "epoch_logs": [                # loss mỗi epoch
                {"epoch": int, "train_loss": float, "val_loss": float}
            ],
            "total_time_seconds": float,
            "early_stopped": bool
        }
    """
```

---

## 10. backend/inference

**Chủ sở hữu: TV6**

```python
def run_inference(
    model: nn.Module,
    input_scaled: torch.Tensor,      # (B, lookback, 1)
    scaler: StandardScaler
) -> np.ndarray:
    """
    Inference: forward pass + inverse transform.
    Không nhận target. Không cập nhật trọng số.

    Returns:
        np.ndarray shape (B, forecast_length) — giá USD gốc
    """
```

---

## 11. backend/evaluation

**Chủ sở hữu: TV6**

```python
def compute_metrics(
    predictions: np.ndarray,     # (N, forecast_length) giá USD
    actuals: np.ndarray,         # (N, forecast_length) giá USD
    horizon_steps: List[int]     # [1] hoặc [1,2,3,4,5]
) -> dict:
    """
    Tính MAE và RMSE trên giá gốc, theo từng horizon step.

    Returns:
        {
            "overall": {"mae": float, "rmse": float, "sample_count": int},
            "per_step": {
                1: {"mae": float, "rmse": float, "sample_count": int},
                ...
            }
        }
    """


def compute_errors(
    predictions: np.ndarray,
    actuals: np.ndarray
) -> np.ndarray:
    """
    Sai số có dấu: e = prediction - actual.
    Returns: np.ndarray cùng shape với input
    """
```

---

## 12. backend/error_analysis

**Chủ sở hữu: TV6**

```python
def analyze_errors(
    predictions: dict,        # {"lstm": np.ndarray, "persistence": np.ndarray, ...}
    actuals: np.ndarray,
    dates: List[str],
    config: dict              # số ví dụ, quy tắc chọn
) -> dict:
    """
    Phân tích lỗi: nhóm theo giai đoạn, trường hợp tốt/kém.

    Returns:
        {
            "summary": {...},
            "best_cases": [...],
            "worst_cases": [...],
            "by_period": {...}
        }
    """
```

---

## 13. backend/artifacts

**Chủ sở hữu: TV6**

```python
def save_checkpoint(model, optimizer, epoch, val_loss, path): ...
def load_checkpoint(path, model_class, **model_kwargs) -> (nn.Module, dict): ...
def save_scaler(scaler, path): ...
def load_scaler(path) -> StandardScaler: ...
def save_run_metadata(run_id, config, metrics, path): ...
def create_release(release_id, components: dict, path): ...
def load_release(release_id, path) -> dict: ...
def verify_release_integrity(release_id, path) -> dict: ...
```

---

## 14. backend/audit

**Chủ sở hữu: TV6**

```python
def audit_split(samples: List[dict]) -> dict:
    """Kiểm tra không rò rỉ dữ liệu giữa train/val/test."""

def audit_scaler(scaler, train_prices, val_prices) -> dict:
    """Kiểm tra scaler chỉ fit trên train."""

def audit_predictions(predictions, run_metadata) -> dict:
    """Kiểm tra dự báo đúng bộ release/checkpoint/scaler."""
```

---

## Quy tắc thay đổi interface

1. Thay đổi signature (thêm/bớt tham số, đổi kiểu trả về) phải thông báo nhóm.
2. Ghi vào `docs/11_Decision_Log.md` với lý do.
3. Cập nhật file này trước khi merge code.
4. Thành viên phụ thuộc interface cũ phải được thông báo để cập nhật.
