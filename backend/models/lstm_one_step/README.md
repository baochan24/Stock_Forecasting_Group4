# models/lstm_one_step

`mean_readout.py` là ablation development TV6: cùng LSTM/4513params, chỉ thaylast hidden bằngmean30hidden. Sáu run không cải thiện nhất quán, nên chưa được chọn thay default hoặc tích hợp release. Không sửa model.py/class export mặc định. Xem reports/audits/TV6_Readout_Ablation.md.

Mục3 TV3 nghiệm thu local23/11/2026: architecture/forward/gradient/state/Adam smoke và file state_dict lưu/nạp sau cập nhật đạt. Suite77/77 tests; gradcheck số học dùng shared forward hidden2/T3 cho input/parameters, default hidden32 có kiểm backward/weights riêng. Output sau reload khớp tuyệt đối, eval không cập nhật weights, một/năm bước không chia sẻ storage. Giữ float64 hiện tại, không đổi code model trong mục3. Chi tiết reports/audits/TV3_Progress.md; chưa training/checkpoint chính thức hoặc sạch/máy khác.

**Dtype hiện tại23/11/2026:** theo yêu cầu người dùng, LSTM/Linear khởi tạo float64 explicit (không đổi global torch dtype). Input/hidden/cell/output/gradient dùng float64; adapter giữ precision TV2, không castfloat32. Suite66/66 và forward toàn bộ5460 mẫu thật đạt. Có thể .float() cho benchmark riêng nhưng không là cấu hình mặc định. Float64 không chứng minh dự báo chính xác hơn; bước Adam tổng hợp CPU đo chậm gần3 lần, xem TV3_Progress.md. Các ghi chú float32/giữ nguyên model.py bên dưới là lịch sử trước thay đổi.

Mục2 TV3 đã có adapter CPU float32 từ TV2 hiện tại tại backend/data/preparation/tensors.py. Dùng make_lstm_inputs cho input-only, make_lstm_training_batch cho X/y training; gọi model chỉ với X. Toàn suite63/63 và forward tất cả5460 mẫu hai modes đã đạt trên source workspace. Không đổi model.py, không checkpoint/training; xem reports/audits/TV3_Progress.md. Các ghi chú mục1 dưới đây giữ theo lịch sử.

LSTM một lớp hidden 32, Linear ra 1 là cấu hình khởi đầu. Định nghĩa mạng và forward.

Trạng thái 23/11/2026: đã tiếp nhận model.py/__init__.py đúng module từ Thien-code137-patch-1, commit `1f209b70c5690fb5e41b3b26d8eab36b2b6c029d`, theo yêu cầu mục 1 TV3. Giữ nguyên thuật toán tác giả, chưa nghiệm thu toàn bộ TV3 hoặc training.

Import từ gốc project: `from backend.models.lstm_one_step import LSTMOneStep`. Default: LSTM1 lớp, input_size1, hidden32, Linear ra1; 4513 tham số. Input tensor float32 `(B,30,1)` cho model mặc định, output `(B,1)`; h/c zero mới mỗi forward. Class còn hỗ trợ T10/60 theo hướng thử nghiệm đã nêu trong thiết kế; không tự chọn lookback.

Toàn suite TV3 55/55 tests đạt local, xem `reports/audits/TV3_Progress.md`. TV2 X/y hiện float64, cần adapter cast ở mục 2; không sửa TV2 hoặc tự fit scaler trong model. Chưa có checkpoint đã train; state_dict roundtrip trong tests là unit test trên trọng số khởi tạo.
