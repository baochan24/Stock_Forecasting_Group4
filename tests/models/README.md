# Kiểm thử mô hình LSTM

Thư mục này chứa các bài kiểm thử cho LSTM One-step, LSTM Multi-step và Model Trace.

## Các file kiểm thử

| File                      | Nội dung                                                                     |
| ------------------------- | ---------------------------------------------------------------------------- |
| `test_lstm_one_step.py`   | Kiểm tra kích thước đầu vào, đầu ra và số tham số của LSTM dự báo một phiên. |
| `test_lstm_multi_step.py` | Kiểm tra mô hình dự báo đồng thời năm phiên trong một lần forward.           |
| `test_lstm_contract.py`   | Kiểm tra gradient, trạng thái độc lập, cập nhật trọng số và lưu/nạp mô hình. |
| `test_lstm_trace.py`      | Đối chiếu các trạng thái và kết quả truy vết với phép tính của PyTorch.      |

## Cách chạy

Tại thư mục gốc của dự án, chạy:

```bash
python -m pytest tests/models/ -v -k lstm
```

## Kết quả

55/55 ca kiểm thử LSTM đã chạy thành công trên CPU. Các bài kiểm thử này dùng tensor mô phỏng nên không cần tải dữ liệu AAPL.

Trước đó, hai mô hình đã được kiểm tra thêm với dữ liệu AAPL `aapl_2015_2025_v1` của TV1 và bản sao preprocessing từ PR #2, #3 của TV2. Cả hai ca kiểm thử tích hợp đều đạt. Bản sao và hai ca kiểm thử tạm thời không còn nằm trong thư mục này.

Khi tích hợp chính thức, mô hình sẽ nhận dữ liệu đã tiền xử lý từ TV2. Cần kiểm tra lại với module chính thức của TV2 và checkpoint do TV4 huấn luyện. Kết quả trên chưa phải kết quả đánh giá độ chính xác dự báo cổ phiếu.
