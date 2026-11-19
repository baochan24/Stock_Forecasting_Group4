# models/lstm_one_step

LSTM một lớp hidden 32, Linear ra 1 là cấu hình khởi đầu. Định nghĩa mạng và forward.

Trạng thái: đã triển khai và kiểm thử độc lập; chưa huấn luyện chính thức cùng TV4.

## TV3 — cập nhật triển khai

Public class giữ đúng mục 5 của
`docs/14_Module_Interfaces.md`:

```python
from backend.models.lstm_one_step import LSTMOneStep

model = LSTMOneStep(input_size=1, hidden_size=32)
```

- Đầu vào: float32 `(B, 30, 1)` theo cấu hình mặc định của TV2.
- `nn.LSTM` một lớp, `batch_first=True`, hidden 32, một chiều, bias mặc định.
- Hai state zero mới `(1, B, 32)` mỗi forward; lấy `sequence[:, -1, :]`.
- `nn.Linear(32, 1)` trả `(B, 1)`, không squeeze, không activation cuối.
- 4.513 tham số mặc định (4.480 LSTM + 33 Linear), đã đếm bằng PyTorch.
- Cùng logic cho lookback 10/30/60; không tự lựa chọn lookback tối ưu.
- Không fit scaler, không nhận target, không train hoặc tính metric tại model.
- `_LSTMRegressor` là logic nội bộ dùng chung với multi-step; không export.

Xem bằng chứng và hướng dẫn kiểm thử tại `tests/models/README.md`.


## Bổ sung kiểm chứng dữ liệu thật

Đã kiểm tra với snapshot AAPL TV1 và logic PR TV2 (bản sao test, có sửa thụt lề).
Xem `tests/models/README.md`. Không phải checkpoint chính thức.
