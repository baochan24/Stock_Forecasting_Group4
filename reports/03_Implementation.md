# Mã nguồn và triển khai

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
