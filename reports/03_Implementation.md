## Mô hình CNN 1D một bước (TV5)

Trạng thái: model đã cài đặt và qua kiểm thử đơn vị. **Chưa huấn luyện, chưa có kết quả thực nghiệm.**

### Vai trò
CNN 1D một bước là mô hình so sánh với LSTM một bước. Cả hai dùng cùng lookback
30 phiên và cùng mục tiêu: giá đóng cửa điều chỉnh của phiên giao dịch kế tiếp.

### Kiến trúc
| Lớp | Cấu hình | Tham số |
|---|---|---|
| Conv1d | 1 → 16 kênh, kernel 3, padding 1 | 64 |
| ReLU | | 0 |
| Conv1d | 16 → 32 kênh, kernel 3, padding 1 | 1.568 |
| ReLU | | 0 |
| MaxPool1d | kích thước 2 (30 → 15 bước) | 0 |
| Flatten + Dropout | 32 × 15 = 480 đặc trưng, dropout 0,1 | 0 |
| Linear | 480 → 32, ReLU | 15.392 |
| Linear | 32 → 1 | 33 |
| **Tổng** | | **17.057** |

### Giao diện
- Input: tensor `(batch, 30, 1)`, giá đã chuẩn hóa bằng StandardScaler fit trên tập train.
- Output: tensor `(batch, 1)` ở thang đã chuẩn hóa. Inverse transform và tính MAE/RMSE
  trên thang USD do module đánh giá thực hiện.
- Model không nhận target, không tự chuẩn hóa, không chứa logic metric.
- Cấu hình ghi/nạp qua `get_config()` và `from_config()`.
- Mã nguồn: `backend/models/cnn_one_step/`; test: `tests/models/test_cnn_one_step.py`.

### Kiểm thử đã chạy
7 test đạt trên CPU (Python 3.14, PyTorch, pytest 9.2): shape đầu ra, từ chối input sai
shape, tái lập khi cùng seed, mẫu trong batch độc lập, gradient chảy tới mọi tham số,
vòng cấu hình, cấu hình không hợp lệ.

### Giả định chờ xác nhận
- Shape input/output theo hợp đồng dữ liệu của TV2 (chưa đối chiếu với docs/04 và docs/14).
- Cách training loop dùng chung của TV4 gọi model và lưu checkpoint.
- Ngân sách tham số so với LSTM của TV3: chưa có số để so sánh.

### Chưa thực hiện
- Huấn luyện bằng training loop của TV4 và ghi thời gian chạy CPU.
- Chạy ba seed định trước và chọn checkpoint theo validation.
- So sánh với LSTM và persistence: chưa kiểm chứng, ghi ở `reports/06_Baseline_and_Model_Comparison.md` khi có kết quả thật.