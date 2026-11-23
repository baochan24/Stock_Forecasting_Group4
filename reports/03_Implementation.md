# Mã nguồn và triển khai

## TV3 — kiến trúc, trace và bàn giao kỹ thuật local

LSTM1 lớp, input_size1/hidden32, batch_first, h/c zero mới mỗi forward. Lấy hidden time step cuối qua Linear1 hoặc5;4513/4645 tham số. Multi-step direct multi-output có weights riêng, không recursive. Model/adapter CPU float64 theo lựa chọn người dùng; không đổi shape/lịch sử/split của TV2. Adapter giữ ID/version/pairing, tách input khỏi targets.

Trace tái dựng gates bằng weights/bias thực, đối chiếu state/forward với rtol1e-10/atol1e-12 float64, no_grad/eval và không thay input/weights/gradients/mode. Đây là phép tính verified, không giải thích thị trường hoặc API đã phê duyệt. Persistence helper kiểm version/source hashes/scaler/horizon/lookback/checksum/actual dtype trước strict load, từ chối diagnostic untrained mặc định.

99/99 tests trên venv sạch, integration5460 samples và trace6 stages trong gói giải nén đã đạt local. Notebook03 ghi từng mục/cells/output; hướng dẫn consumer docs/TV3_Handoff_TV4_TV6.md, kết quả reports/audits/TV3_Final_Handoff.md. Chưa có training/checkpoint AAPL hoặc metric; TV4 làm training/selection, TV6 release/inference/eval. Không kết luận LSTM/CNN vượt persistence từ tests kỹ thuật.

## TV2 — preprocessing và bàn giao local (22/11/2026)

Pipeline hiện có: accept snapshot TV1/hash/provenance → gán split theo ngày target → fit scaler trên toàn train 2015–2022 → lưu/nạp scaler → tạo windows1/5 từ lịch sử liên tục → kiểm contract/input-only → audit leakage → đóng gói/tái lập. Code thuộc backend/data/preparation, backend/data/transforms, backend/artifacts (persistence) và backend/audit; không gọi model/training/API.

X float64 (B,30,1), y float64 (B,1)/(B,5), raw USD và ngày/ID/version giữ trong records input/target riêng. Lịch sử từ split trước được dùng khi đã quan sát; 5 target phải cùng split. Scaler chỉ fit train, mọi đường load/verify/inference adapter không refit. Tạo tensor model cần adapter riêng.

51/51 tests và kiểm tra ZIP giải nén độc lập bằng venv sạch đã đạt; X/y/indices nạp lại bằng dựng mới, hashes giữ nguyên. Chi tiết artifacts/lệnh/logs/giới hạn: docs/TV2_Setup_and_Handoff.md và reports/audits/TV2_Final_Handoff.md. Chưa có xác nhận máy khác hoặc thực nghiệm model; không suy ra LSTM/CNN hiệu quả từ tests preprocessing.

Trạng thái: đã có implementation phần dữ liệu TV1 trong workspace; model/training/API/web chưa được nghiệm thu trong phần việc này.

## Implementation TV1 hiện tại

- `backend/data/acquisition/downloader.py`: snapshot AAPL 2015–2025, metadata/hash, từ chối version trùng và exclusive creation.
- `backend/data/validation/provenance.py`: khai báo nguồn/version/AAPL/USD/phạm vi/chính sách/hash khớp raw.
- `backend/data/validation/validator.py`: ngày/giá/trùng/thứ tự/lịch phiên/OHLCV, cảnh báo giữ biến động lớn, xuất bảng chuẩn không ghi đè.
- `backend/data/validation/standard_output.py`: nghiệm thu schema/ngày/giá/hash sau audit chất lượng.
- `scripts/`: verify/package, runner tests, build/execute notebook và kiểm chứng workspace riêng; hướng dẫn tại `docs/TV1_Setup_and_Reproduce.md`.
- `tests/data/`: 34 test methods và nhiều subcase; fixture tổng hợp/mock mạng được tách khỏi kiểm tra artifacts thật.

Notebook trình bày flow hạng mục 1–10 và bảng tổng audit; không fit scaler/windowing hoặc training. Không coi metadata/hash là xác thực độc lập sàn, hoặc workspace riêng cùng máy là máy thành viên khác.

## Nội dung cần hoàn thiện

Điền bằng hoạt động thực tế trong đúng phạm vi Define/Design.

## Bằng chứng

Liên kết dataset version, run/release, logs, audit và phép kiểm tra liên quan khi có. Không điền số liệu giả hoặc kết luận trước thực nghiệm.
