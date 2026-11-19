# Mã nguồn và triển khai

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
