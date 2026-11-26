# models/lstm_multi_step

Mục3 TV3 đã nghiệm thu local23/11/2026 cùng one-step: kiến trúc/forward/gradient64, state độc lập, file state_dict roundtrip sau Adam và chống nhầm horizon; update one-step không làm đổi model5-step. Suite77/77 đạt, evidence trong TV3_Progress.md. Đây là tests tổng hợp, không chứng nhận checkpoint đã train hoặc metric; không đổi kiến trúc/default dtype64.

**Dtype hiện tại23/11/2026:** model mặc định và adapter dùng CPU float64 xuyên suốt; không đổi kiến trúc/shape, vẫn trọng số riêng và direct5 outputs. Trace/state_dict/backward đã chạy với float64, suite66/66 đạt; mẫu TV2 thật không downcast và artifacts giữ nguyên. Chi phí Adam step tổng hợp gần3.13 lần float32 trên máy thử, không là dự đoán thời gian train hoặc độ chính xác. Mô tả float32 bên dưới là lịch sử, xem TV3_Progress.md cập nhật.

Mục2 TV3: adapter TV2 chính thức cast X/y float32 CPU, kiểm ID/version/pairing và horizon5; model chỉ nhận X. Tất cả1980/246/498 mẫu multi-step đã forward/inverse finite với trọng số khởi tạo, không metric/huấn luyện. Toàn suite63/63 đạt; adapter backend/data/preparation/tensors.py, bằng chứng reports/audits/TV3_Progress.md. Các trạng thái mục1 bên dưới là lịch sử.

LSTM hidden 32, Linear ra 5; direct multi-output, checkpoint riêng.

Trạng thái 23/11/2026: đã tiếp nhận model.py/__init__.py đúng module từ commit Thiện `1f209b70c5690fb5e41b3b26d8eab36b2b6c029d`, giữ nguyên source. Mục 1 TV3 đạt local, chưa hoàn thành các mục tiếp theo.

`from backend.models.lstm_multi_step import LSTMMultiStep`. Default LSTM1 lớp hidden32, Linear5, 4645 tham số; input float32 `(B,30,1)`→output `(B,5)`. Chỉ forecast_length=5; direct multi-output, không recursive, mỗi instance có trọng số riêng. Dùng lõi `_LSTMRegressor` từ module one-step nhưng không chia sẻ trọng số. Không scaler/training/metric trong model.

Suite55/55 tests đạt local; tích hợp TV2 chính thức/dtype adapter còn mục 2. Model multi-step cần được TV4 train riêng với checkpoint riêng; test optimizer smoke không phải training chính thức.
