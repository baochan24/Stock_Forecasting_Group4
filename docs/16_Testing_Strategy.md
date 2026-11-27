# Testing Strategy

Phiên bản: 1.0 — 13/11/2026
Trạng thái: bản đặc tả trước triển khai. Bổ sung test cụ thể khi từng module được code.

---

## 1. Framework và công cụ

| Công cụ | Mục đích |
|---|---|
| `pytest` | Chạy tất cả test |
| `assert` / `pytest.approx` | So sánh số học có dung sai |

Chạy test:

```bash
# Toàn bộ
pytest tests/ -v

# Một thư mục
pytest tests/data/ -v

# Một file
pytest tests/data/test_preparation.py -v
```

## 2. Cấu trúc thư mục test

```
tests/
├── conftest.py                  # fixtures dùng chung
├── data/
│   ├── test_acquisition.py
│   ├── test_validation.py
│   ├── test_preparation.py
│   └── test_transforms.py
├── models/
│   ├── test_lstm_one_step.py
│   ├── test_lstm_multi_step.py
│   └── test_cnn_one_step.py
├── training/
│   └── test_training_loop.py
├── evaluation/
│   ├── test_metrics.py
│   └── test_error_analysis.py
├── api/
│   └── test_endpoints.py
└── integration/
    ├── test_pipeline_one_step.py
    └── test_pipeline_multi_step.py
```

## 3. Quy ước đặt tên

| Quy ước | Ví dụ |
|---|---|
| File test | `test_{module_name}.py` |
| Hàm test | `test_{hành_vi_cần_kiểm_tra}` |
| Class nhóm test | `TestClassName` (không bắt buộc) |

```python
# tests/models/test_lstm_one_step.py

def test_forward_output_shape():
    """Output shape phải là (B, 1) khi input shape (B, 30, 1)."""

def test_forward_output_finite():
    """Output không chứa NaN hoặc Inf."""

def test_forward_batch_size_one():
    """Model hoạt động với batch_size=1."""
```

## 4. Test theo module và chủ sở hữu

### 4.1. Data — TV1, TV2

| Test | Module | Mô tả |
|---|---|---|
| Đọc CSV đúng format | acquisition | Đọc được file, đúng cột, đúng kiểu |
| Không ngày trùng | validation | Không có hai dòng cùng ngày |
| Giá dương | validation | Tất cả adjusted_close > 0 |
| Ngày tăng dần | validation | Cột date sắp tăng dần |
| Split đúng khoảng | preparation | Train targets trong 2015–2022, val trong 2023, test trong 2024–2025 |
| Scaler fit trên train | preparation | `scaler.mean_` và `scaler.scale_` khớp với giá train |
| Scaler không fit val/test | preparation | Transform val/test dùng scaler train, không fit lại |
| Window shape đúng | preparation | Input shape (lookback,), target shape (forecast_length,) |
| Không rò rỉ target vào input | preparation | Ngày target > ngày cuối input |
| Multi-step cùng tập | preparation | 5 target nằm cùng split |
| Scale/inverse đối xứng | transforms | `inverse_scale(scale(x)) ≈ x` |

### 4.2. Models — TV3, TV5

| Test | Module | Mô tả |
|---|---|---|
| Output shape (B, 1) | lstm_one_step | Input (B, 30, 1) → output (B, 1) |
| Output shape (B, 5) | lstm_multi_step | Input (B, 30, 1) → output (B, 5) |
| Output shape (B, 1) | cnn_one_step | Input đúng convention → output (B, 1) |
| Output hữu hạn | tất cả model | `torch.isfinite(output).all()` |
| Batch size = 1 hoạt động | tất cả model | Không lỗi khi B=1 |
| Batch size lớn | tất cả model | Không lỗi khi B=128 |
| Gradient flows | tất cả model | `output.sum().backward()` không lỗi, gradient != 0 |
| Số tham số ghi nhận | tất cả model | In số tham số, đối chiếu với thiết kế |

### 4.3. Training — TV4

| Test | Module | Mô tả |
|---|---|---|
| Loss giảm sau N epoch | training | Trên dữ liệu nhỏ, loss epoch N < loss epoch 0 |
| Early stopping hoạt động | training | Dừng trước max_epochs khi val_loss không giảm |
| Checkpoint lưu/nạp | training | Nạp lại checkpoint, forward pass cho cùng output |
| Epoch logs đúng format | training | CSV có đủ cột, số dòng = số epoch đã chạy |
| Seed tái lập | training | Cùng seed + cùng dữ liệu → cùng loss (trên cùng máy) |

### 4.4. Evaluation — TV6

| Test | Module | Mô tả |
|---|---|---|
| MAE tính tay | evaluation | So sánh với ví dụ tính tay đơn giản |
| RMSE tính tay | evaluation | `sqrt(mean([1,2,3]²))` = kết quả mong đợi |
| Persistence MAE/RMSE | baselines + evaluation | Persistence trên 3 mẫu tay → đúng kết quả |
| Cùng tập mẫu | evaluation | Lỗi nếu predictions và actuals khác length |
| Multi-step từng bước | evaluation | Per-step metric khác overall metric |

### 4.5. Integration

| Test | Mô tả |
|---|---|
| Pipeline one-step | Data → split → scale → window → model → inference → inverse → metric → không lỗi |
| Pipeline multi-step | Tương tự, forecast_length=5 |
| Release nạp lại | Tạo release → nạp lại → inference → cùng kết quả |

## 5. Fixtures dùng chung (conftest.py)

```python
# tests/conftest.py
import pytest
import numpy as np
import torch

@pytest.fixture
def sample_prices():
    """100 giá giả để test, không phải dữ liệu AAPL thật."""
    np.random.seed(42)
    return 100 + np.cumsum(np.random.randn(100) * 0.5)

@pytest.fixture
def sample_dates():
    """100 ngày giao dịch giả."""
    import pandas as pd
    return pd.bdate_range("2020-01-01", periods=100).strftime("%Y-%m-%d").tolist()

@pytest.fixture
def sample_input_tensor():
    """Tensor input mẫu shape (4, 30, 1)."""
    return torch.randn(4, 30, 1)
```

## 6. Quy tắc

- **Chạy test trước khi bàn giao code.** Không bàn giao code mà test fail.
- **Không dùng dữ liệu AAPL thật trong unit test.** Dùng dữ liệu giả nhỏ. Test với dữ liệu thật là integration test.
- **Không dùng test để tuning.** Test kiểm tra tính đúng, không phải chất lượng dự báo.
- **Dung sai số học:** dùng `pytest.approx(expected, abs=1e-6)` cho so sánh float.
- **Mỗi thành viên viết test cho module của mình.** TV6 viết thêm integration test.
- **Test phải chạy nhanh** (dưới 30 giây cho toàn bộ unit test). Integration test có thể lâu hơn.

## 7. Khi nào chạy test

| Thời điểm | Loại test |
|---|---|
| Sau mỗi thay đổi code | Unit test của module liên quan |
| Trước khi bàn giao | Toàn bộ unit test |
| Khi tích hợp module | Integration test |
| Khi đánh giá cuối | Toàn bộ test suite |
