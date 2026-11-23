# TV3 — dọn file dư trên nhánh Thiên

Ngày 23/11/2026, theo yêu cầu người dùng xóa file dư trên nhánh `Thien-code137-patch-1`. Base đã đối chiếu GitHub: `75947bf80e56e9549418fdedc2e52e2446f61177`.

## Phạm vi

Loại 9 file upload cũ: `README.md`, `__init__.py`, `model.py` trong mỗi thư mục gốc `lstm_one_step/`, `lstm_multi_step/`; và `README.md`, `__init__.py`, `lstm_trace.py` trong `model_trace/`.

Các bản hiện hành tương ứng nằm ở `backend/models/lstm_one_step/`, `backend/models/lstm_multi_step/`, `backend/model_trace/`. Bản cũ không còn đúng layout và chưa mang các cập nhật float64 của source đã nghiệm thu. Đối chiếu imports trong backend/tests/scripts không có dependency vào ba package ở gốc. Xóa bản cũ tránh người dùng import nhầm model.

Giữ nguyên các module TV1/TV2 mà adapter cần, tests, notebook, tài liệu thiết kế/audit và các README nền TV4–TV6. Không xóa theo tiêu chí thư mục hiện chưa có implementation. Không đổi mô hình/shape/dtype, dữ liệu/artifacts hoặc nội dung cell notebook; không tạo lại outputs cho thay đổi chỉ về cấu trúc dư thừa.

## Kiểm chứng

Đã chạy lại `scripts/run_tv3_checks.py --require-clean` từ checkout đã xóa file, bằng venv CPU sạch: **99/99 tests đạt**, 0 fail/error/skip. Receipt local: `.venv/tv3_publish_20261123/logs/audit/tv3_tests_20261123T034005120163Z/summary.json`. Trạng thái push đối chiếu GitHub thực tế. Mọi file xóa vẫn có thể truy xuất từ lịch sử Git; không rewrite history hoặc force push.
