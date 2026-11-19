# data/validation

Kiểm tra ngày, thiếu/trùng, giá trị; trả báo cáo và dữ liệu hợp lệ. Dùng chung phép kiểm tra với audit.

`validator.py` kiểm tra schema, ngày, thiếu/trùng/thứ tự, NaN/Inf/giá không dương, lịch phiên và độ phủ, OHLCV nếu có; trả lỗi thay vì sửa/xóa dòng. Biến động >10% được giữ lại và gắn cảnh báo để điều tra. `provenance.py` kiểm tra metadata/hash trước khi xuất validated. Không ghi đè validated/report đã tồn tại.

Hai file validated/report được tạo exclusive; nếu gặp lỗi bắt được khi ghi, chỉ xóa file do chính lần gọi tạo ra để không để bộ output dở. Trường hợp process bị kill/mất điện vẫn cần kiểm tra thủ công; không cung cấp overwrite để che lỗi.

Lịch `NASDAQ` do exchange_calendars cung cấp hiện là alias `XNYS`; báo cáo ghi rõ lịch thực tế, phiên bản thư viện và giới hạn tham chiếu. Dependencies có trong `notebooks/requirements-eda.txt`. Notebook gọi chung phép kiểm tra, không tự viết pipeline khác.

Chạy tests trên snapshot đã bàn giao: đặt `TV1_DATASET_VERSION` bằng version cần kiểm tra rồi chạy `python -m unittest discover -s tests/data -v`. Không đặt biến thì test artifacts thật được skip rõ ràng; tests fixture vẫn chạy.
