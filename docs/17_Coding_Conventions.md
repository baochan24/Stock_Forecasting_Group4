# Coding Conventions

Phiên bản: 1.0 — 13/11/2026
Trạng thái: quy ước chung cho cả nhóm. Áp dụng khi bắt đầu code.

---

## 1. Style chung

- Tuân thủ **PEP 8**.
- Dùng **`ruff`** để lint và format (thay thế flake8 + black + isort).
- Độ rộng dòng tối đa: **88 ký tự** (mặc định của ruff/black).
- Indent: **4 spaces**, không dùng tab.
- Encoding: **UTF-8**.

Cấu hình ruff (đặt trong `pyproject.toml` ở gốc project):

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]   # errors, pyflakes, warnings, isort

[tool.ruff.format]
quote-style = "double"
```

Chạy:

```bash
# Kiểm tra
ruff check backend/ tests/

# Tự động sửa
ruff check --fix backend/ tests/

# Format
ruff format backend/ tests/
```

## 2. Đặt tên

| Đối tượng | Quy ước | Ví dụ |
|---|---|---|
| Module / file | `snake_case` | `lstm_one_step.py`, `data_preparation.py` |
| Function / method | `snake_case` | `create_windows()`, `compute_metrics()` |
| Class | `PascalCase` | `LSTMOneStep`, `CNNOneStep` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_EPOCHS`, `DEFAULT_LOOKBACK` |
| Variable | `snake_case` | `train_prices`, `val_loss` |
| Private | prefix `_` | `_validate_input()`, `_hidden_size` |
| File test | `test_{module}.py` | `test_preparation.py` |
| Hàm test | `test_{hành_vi}` | `test_forward_output_shape` |

### Tên biến thường dùng trong project

| Tên | Ý nghĩa | Kiểu |
|---|---|---|
| `prices` | Giá gốc USD | `np.ndarray` |
| `scaled_prices` | Giá đã chuẩn hóa | `np.ndarray` |
| `dates` | Danh sách ngày | `List[str]` |
| `lookback` | Số phiên input | `int` |
| `forecast_length` | Số bước dự báo (1 hoặc 5) | `int` |
| `scaler` | StandardScaler đã fit | `StandardScaler` |
| `model` | Mô hình PyTorch | `nn.Module` |
| `train_loader` | DataLoader tập train | `DataLoader` |
| `val_loader` | DataLoader tập validation | `DataLoader` |
| `predictions` | Giá dự báo USD | `np.ndarray` |
| `actuals` | Giá thực tế USD | `np.ndarray` |
| `run_id` | ID duy nhất của run | `str` |
| `release_id` | ID bộ phát hành | `str` |

## 3. Docstring

Dùng **Google style**:

```python
def create_windows(
    dates: List[str],
    prices: np.ndarray,
    scaler: StandardScaler,
    lookback: int = 30,
    forecast_length: int = 1,
) -> dict:
    """Tạo cửa sổ input-target từ chuỗi giá.

    Chia chuỗi giá thành các cửa sổ trượt với lookback phiên input
    và forecast_length phiên target.

    Args:
        dates: Danh sách ngày phiên giao dịch, format YYYY-MM-DD.
        prices: Giá đóng cửa đã điều chỉnh, shape (N,).
        scaler: StandardScaler đã fit trên tập train.
        lookback: Số phiên input. Mặc định 30.
        forecast_length: Số bước dự báo, 1 hoặc 5. Mặc định 1.

    Returns:
        Dict chứa danh sách samples và metadata.
        Xem chi tiết tại docs/14_Module_Interfaces.md.

    Raises:
        ValueError: Nếu len(prices) < lookback + forecast_length.
    """
```

Tối thiểu:
- Mỗi hàm public phải có docstring.
- Ghi rõ Args, Returns. Raises nếu có.
- Hàm private (`_`) có docstring ngắn cũng được.

## 4. Type Hints

**Khuyến khích mạnh** (không bắt buộc 100% nhưng nên có cho mọi hàm public):

```python
# Tốt
def compute_metrics(
    predictions: np.ndarray,
    actuals: np.ndarray,
    horizon_steps: List[int],
) -> dict:

# Chấp nhận được nhưng nên bổ sung
def compute_metrics(predictions, actuals, horizon_steps):
```

Import typing:

```python
from typing import List, Dict, Optional, Tuple
```

## 5. Import

Thứ tự import (ruff tự sắp xếp với rule `I`):

```python
# 1. Standard library
import os
import json
from pathlib import Path

# 2. Third-party
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

# 3. Local / project
from backend.data.transforms import scale, inverse_scale
from backend.models.lstm_one_step import LSTMOneStep
```

Quy tắc:
- Không `import *`.
- Ưu tiên import cụ thể (`from x import y`) hơn import toàn module khi chỉ dùng một vài thứ.

## 6. Cấu trúc file module

```python
"""Mô tả ngắn module này làm gì.

Chi tiết hơn nếu cần.
"""

# Imports (theo thứ tự trên)

# Constants
DEFAULT_LOOKBACK = 30
DEFAULT_FORECAST_LENGTH = 1

# Classes (nếu có)
class LSTMOneStep(nn.Module):
    ...

# Public functions
def create_windows(...):
    ...

# Private helpers
def _validate_dates(...):
    ...
```

## 7. Logging

Dùng **`logging`** module, không dùng `print` trong code production:

```python
import logging

logger = logging.getLogger(__name__)

# Trong hàm
logger.info("Training started: run_id=%s, seed=%d", run_id, seed)
logger.warning("NaN detected in loss at epoch %d", epoch)
logger.error("Checkpoint not found: %s", path)
```

`print()` chỉ dùng trong:
- Notebooks (khảo sát, demo)
- Scripts entry point (output cho người dùng)

## 8. Error Handling

```python
# Dùng built-in exceptions với message rõ ràng
if lookback < 1:
    raise ValueError(f"lookback must be >= 1, got {lookback}")

if not path.exists():
    raise FileNotFoundError(f"Checkpoint not found: {path}")

# Không bắt exception chung chung rồi bỏ qua
# ❌ Sai
try:
    result = do_something()
except:
    pass

# ✅ Đúng
try:
    result = do_something()
except SpecificError as e:
    logger.error("Failed: %s", e)
    raise
```

## 9. Cấu trúc `__init__.py`

Mỗi module package có `__init__.py` export các hàm/class public:

```python
# backend/models/lstm_one_step/__init__.py
from backend.models.lstm_one_step.model import LSTMOneStep

__all__ = ["LSTMOneStep"]
```

Giữ `__init__.py` ngắn gọn — chỉ import và export, không chứa logic.

## 10. Đường dẫn file

Dùng **`pathlib.Path`**, không nối string:

```python
# ✅ Đúng
from pathlib import Path

checkpoint_dir = Path("artifacts") / "checkpoints"
file_path = checkpoint_dir / f"{run_id}_best.pt"

# ❌ Tránh
file_path = "artifacts/checkpoints/" + run_id + "_best.pt"
```

## 11. Số magic

Không dùng số magic trong code — đặt constant hoặc lấy từ config:

```python
# ❌ Sai
model = LSTMOneStep(1, 32)
for epoch in range(100):

# ✅ Đúng
model = LSTMOneStep(
    input_size=config["model"]["input_size"],
    hidden_size=config["model"]["hidden_size"],
)
for epoch in range(config["training"]["max_epochs"]):
```

## 12. Git commit message

```
<type>: <mô tả ngắn>

<mô tả chi tiết nếu cần>
```

Type:
| Type | Khi nào |
|---|---|
| `feat` | Thêm tính năng mới |
| `fix` | Sửa lỗi |
| `docs` | Cập nhật tài liệu |
| `test` | Thêm/sửa test |
| `refactor` | Tái cấu trúc, không đổi hành vi |
| `config` | Thay đổi cấu hình |

Ví dụ:
```
feat: add LSTM one-step model with forward pass
docs: update module interfaces for preparation
test: add shape tests for LSTM multi-step
fix: correct scaler inverse transform for multi-step
```

## 13. Checklist trước khi bàn giao

- [ ] Code chạy không lỗi
- [ ] `ruff check` không warning
- [ ] `ruff format` đã chạy
- [ ] Có docstring cho mọi hàm/class public
- [ ] Test pass
- [ ] Không chứa `print()` debug
- [ ] Không chứa đường dẫn tuyệt đối cá nhân
- [ ] Không chứa API key hoặc thông tin bí mật
- [ ] Commit message rõ ràng
