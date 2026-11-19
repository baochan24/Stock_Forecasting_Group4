# models/lstm_multi_step

LSTM hidden 32, Linear ra 5; direct multi-output, checkpoint riêng.

Trạng thái: đã triển khai và kiểm thử độc lập; chưa huấn luyện chính thức cùng TV4.

## TV3 — cập nhật triển khai

`model.py` và `__init__.py`
export class theo mục 6 của `docs/14_Module_Interfaces.md`:

```python
from backend.models.lstm_multi_step import LSTMMultiStep

model = LSTMMultiStep(input_size=1, hidden_size=32, forecast_length=5)
```

Một forward: `(B,30,1)` → LSTM `(B,30,32)` → last hidden `(B,32)` →
Linear `(B,5)`. Từng phần tử là H1 đến H5 trên thang chuẩn hóa.
Đây là direct multi-output, không recursive, không dùng mô hình one-step
đã train để dự báo năm bước. Tái sử dụng code kiến trúc nội bộ, nhưng mỗi
instance có trọng số riêng; cần huấn luyện từ đầu và checkpoint riêng.
Số tham số: 4.645 (4.480 LSTM + 165 Linear). Chỉ chấp nhận horizon=5 theo
phạm vi đã chốt; số lớp cố định 1. TV4 xử lý tensor target và training.

Xem `tests/models/README.md` để kiểm tra kết quả unit test.


## Bổ sung kiểm chứng dữ liệu thật

Đã kiểm tra với snapshot AAPL TV1 và logic PR TV2 (bản sao test, có sửa thụt lề).
Xem `tests/models/README.md`. Không phải checkpoint chính thức.
