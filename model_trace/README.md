# model_trace

Truy vết inference hoặc batch đại diện. Phân biệt phép tính thật/minh họa; không tự cập nhật model phục vụ web.

Trạng thái: đã triển khai và kiểm thử độc lập;

## TV3 — triển khai đề xuất

`lstm_trace.py` export `trace_lstm(model, x)`. Chỉ nhận một cửa sổ đã
chuẩn hóa `(1,T,1)`, không nhận dữ liệu target. TV6 nạp đúng model/checkpoint,
chuyển `eval()` rồi gọi. Chưa có checkpoint nghiên cứu chính thức.

Thuật toán dùng trọng số `weight_ih_l0`, `weight_hh_l0`, hai bias của chính
`nn.LSTM`; tách gate theo thứ tự PyTorch i/f/g/o; tính sigmoid/tanh, cập nhật
cell và hidden state. So sánh hidden/cell từng bước với `nn.LSTM` chạy từng
phiên, cả chuỗi hidden với forward LSTM đầy đủ, state cuối và Linear output
với forward model. `rtol=1e-5`, `atol=1e-6`; sai khác hoặc NaN/Inf gây lỗi,
không trả trace nếu đối chiếu thất bại. Gate là giá trị tái tính theo công
thức, không phải tensor gate được hook trực tiếp từ kernel PyTorch.

Dữ liệu trả về serializable JSON: `input_shape`, `input_scaled`,
`output_shape`, `prediction_scaled`, `initial_hidden`, `initial_cell`,
`steps` (time_step, 4 gate/candidate, hidden_state, cell_state),
`linear_input`, `verification` (dung sai, max absolute errors).
Trace không tự inverse scale, không gắn ngày, không suy diễn ý nghĩa
kinh tế của chiều hidden, không đổi mode/weights/gradient của model.
Các field, giới hạn một mẫu và dung sai là đề xuất của TV3; cần TV6 duyệt
trước khi dùng làm API/schema chính thức (docs/10_Open_Decisions.md).

```python
import torch
from backend.models.lstm_one_step import LSTMOneStep
from backend.model_trace import trace_lstm

# Chỉ minh họa kỹ thuật trên dữ liệu tổng hợp, không phải dự báo AAPL.
model = LSTMOneStep().eval()
trace = trace_lstm(model, torch.zeros(1, 30, 1))
assert trace["verification"]["passed"]
```

Kết quả kiểm thử chi tiết: `tests/models/README.md`.

## Bổ sung kiểm chứng dữ liệu thật

Đã kiểm tra với snapshot AAPL TV1 và logic PR TV2 (bản sao test, có sửa thụt lề).
Xem `tests/models/README.md`. Không phải checkpoint chính thức.
