# Experiment Config Schema

Phiên bản: 1.0 — 13/11/2026
Trạng thái: bản đặc tả trước triển khai. Schema có thể điều chỉnh khi triển khai nhưng phải ghi Decision Log.

Tài liệu này định nghĩa **cấu trúc file cấu hình thực nghiệm** và **quy ước đặt tên** để TV4, TV5 và các thành viên khác dùng chung khi chạy training.

---

## 1. Định dạng

- File cấu hình dùng **YAML** (dễ đọc, dễ comment).
- Đặt trong `experiments/configs/`.
- Mỗi file là một cấu hình thực nghiệm; một cấu hình có thể được chạy với nhiều seed.

## 2. Schema cấu hình

```yaml
# experiments/configs/lstm_one_step_baseline.yaml

# === Thông tin chung ===
experiment_name: "lstm_one_step_baseline"
description: "LSTM một bước, cấu hình khởi đầu theo thiết kế"
model_type: "lstm_one_step"          # lstm_one_step | lstm_multi_step | cnn_one_step

# === Dữ liệu ===
data:
  dataset_version: "v1"              # phiên bản snapshot
  ticker: "AAPL"
  lookback: 30                       # số phiên input
  forecast_length: 1                 # 1 hoặc 5

# === Model ===
model:
  input_size: 1
  hidden_size: 32
  num_layers: 1
  # Thêm field tùy model_type:
  # CNN: num_filters, kernel_size, ...

# === Training ===
training:
  batch_size: 32
  optimizer: "adam"
  learning_rate: 0.001
  loss_function: "mse"
  max_epochs: 100
  early_stopping:
    patience: 10
    monitor: "val_loss"              # metric theo dõi
    mode: "min"
  gradient_clipping: null            # null = không clip; float = ngưỡng

# === Seeds ===
seeds: [42, 123, 456]               # ba seed định trước cho cấu hình cuối

# === Output ===
output:
  checkpoint_dir: "artifacts/checkpoints"
  log_dir: "experiments/runs"
```

## 3. Các field bắt buộc

| Field | Kiểu | Mô tả |
|---|---|---|
| `experiment_name` | str | Tên duy nhất của cấu hình |
| `model_type` | str | `lstm_one_step`, `lstm_multi_step`, `cnn_one_step` |
| `data.dataset_version` | str | Phiên bản snapshot dữ liệu |
| `data.lookback` | int | Số phiên input |
| `data.forecast_length` | int | 1 hoặc 5 |
| `model.input_size` | int | Luôn là 1 (một đặc trưng) |
| `model.hidden_size` | int | Kích thước hidden state |
| `training.batch_size` | int | |
| `training.learning_rate` | float | |
| `training.max_epochs` | int | |
| `training.early_stopping.patience` | int | |
| `seeds` | List[int] | Ít nhất một seed |

## 4. Quy ước đặt tên run_id

```
{model_type}__{experiment_name}__seed{seed}__{timestamp}
```

Ví dụ:
```
lstm_one_step__baseline__seed42__20261115_143022
lstm_multi_step__baseline__seed123__20261115_150510
cnn_one_step__small_cnn__seed456__20261116_091200
```

Quy tắc:
- Dùng dấu `__` (hai gạch dưới) phân tách các phần.
- Timestamp theo format `YYYYMMDD_HHMMSS` (giờ local).
- Tự động sinh bởi experiment runner, không đặt tay.

## 5. Cấu trúc output mỗi run

```
experiments/runs/{run_id}/
├── config.yaml              # bản sao cấu hình đã dùng
├── metadata.json            # thông tin môi trường, git commit, thời gian
├── epoch_logs.csv           # epoch, train_loss, val_loss
├── predictions/
│   ├── val_predictions.csv  # dự báo trên validation
│   └── test_predictions.csv # dự báo trên test (chỉ khi đánh giá cuối)
├── metrics/
│   ├── val_metrics.json     # MAE/RMSE validation
│   └── test_metrics.json    # MAE/RMSE test
└── audit/
    └── audit_report.json    # kết quả kiểm tra
```

## 6. File metadata.json

```json
{
    "run_id": "lstm_one_step__baseline__seed42__20261115_143022",
    "experiment_name": "baseline",
    "model_type": "lstm_one_step",
    "seed": 42,
    "dataset_version": "v1",
    "dataset_hash": "sha256:abc123...",
    "scaler_path": "artifacts/scalers/scaler_v1.pkl",
    "checkpoint_path": "artifacts/checkpoints/lstm_one_step__baseline__seed42__best.pt",
    "python_version": "3.11.5",
    "torch_version": "2.1.0+cpu",
    "git_commit": "a1b2c3d",
    "git_dirty": false,
    "start_time": "2026-11-15T14:30:22",
    "end_time": "2026-11-15T14:45:10",
    "total_time_seconds": 888.0,
    "best_epoch": 67,
    "best_val_loss": 0.00234,
    "early_stopped": true,
    "hostname": "DESKTOP-ABC123",
    "cpu_info": "Intel i5-12400"
}
```

## 7. File epoch_logs.csv

```csv
epoch,train_loss,val_loss,learning_rate,time_seconds
1,0.05234,0.04891,0.001,12.3
2,0.04102,0.03988,0.001,12.1
...
```

## 8. File predictions CSV

```csv
sample_id,forecast_origin,horizon_step,target_date,predicted_price,actual_price,split
s_0001,2023-01-30,1,2023-01-31,152.34,151.89,val
s_0002,2023-01-31,1,2023-02-01,151.89,153.12,val
```

## 9. Ví dụ cấu hình cho từng model

### LSTM one-step (cấu hình khởi đầu)

```yaml
experiment_name: "lstm_one_step_baseline"
model_type: "lstm_one_step"
data:
  dataset_version: "v1"
  ticker: "AAPL"
  lookback: 30
  forecast_length: 1
model:
  input_size: 1
  hidden_size: 32
  num_layers: 1
training:
  batch_size: 32
  optimizer: "adam"
  learning_rate: 0.001
  loss_function: "mse"
  max_epochs: 100
  early_stopping:
    patience: 10
    monitor: "val_loss"
    mode: "min"
  gradient_clipping: null
seeds: [42, 123, 456]
output:
  checkpoint_dir: "artifacts/checkpoints"
  log_dir: "experiments/runs"
```

### LSTM multi-step

```yaml
experiment_name: "lstm_multi_step_baseline"
model_type: "lstm_multi_step"
data:
  dataset_version: "v1"
  ticker: "AAPL"
  lookback: 30
  forecast_length: 5
model:
  input_size: 1
  hidden_size: 32
  num_layers: 1
training:
  batch_size: 32
  optimizer: "adam"
  learning_rate: 0.001
  loss_function: "mse"
  max_epochs: 100
  early_stopping:
    patience: 10
    monitor: "val_loss"
    mode: "min"
  gradient_clipping: null
seeds: [42, 123, 456]
output:
  checkpoint_dir: "artifacts/checkpoints"
  log_dir: "experiments/runs"
```

### CNN one-step (chờ chốt kiến trúc)

```yaml
experiment_name: "cnn_one_step_v1"
model_type: "cnn_one_step"
data:
  dataset_version: "v1"
  ticker: "AAPL"
  lookback: 30
  forecast_length: 1
model:
  input_size: 1
  # CNN-specific — TV5 đề xuất trước triển khai:
  # num_filters: ?
  # kernel_size: ?
  # num_conv_layers: ?
  # pool_type: ?
training:
  batch_size: 32
  optimizer: "adam"
  learning_rate: 0.001
  loss_function: "mse"
  max_epochs: 100
  early_stopping:
    patience: 10
    monitor: "val_loss"
    mode: "min"
  gradient_clipping: null
seeds: [42, 123, 456]
output:
  checkpoint_dir: "artifacts/checkpoints"
  log_dir: "experiments/runs"
```

## 10. Quy tắc

- Không chạy thực nghiệm mà không có file config.
- Không sửa config sau khi run đã bắt đầu — tạo config mới nếu cần thay đổi.
- Bản sao config được lưu trong thư mục run để đảm bảo tái lập.
- Thêm field mới vào schema phải cập nhật file này.
