# Kiểm tra dự kiến: data

Kiểm tra window/split/scaler/ngày, ví dụ bằng tay một/năm bước.

## TV1 — bộ kiểm thử thực thi

Chạy từ gốc repo bằng `.venv/eda/Scripts/python.exe scripts/run_tv1_checks.py --dataset-version <version>`. Cần đủ raw/metadata/validated/validation report và receipt `_complete.json` trỏ gói ZIP của version đó. Lệnh trả exit code khác 0 nếu fail/error/skip hoặc 4 artifacts nguồn thay đổi.

Suite TV1 hiện gồm 34 test methods (có nhiều subcase): pipeline cơ bản/artifacts thật 4; quality 7; provenance 4; versioning 5; standard output 4; handoff integrity 6; pipeline tích hợp offline 4. Audit cuối bổ sung hồi quy lỗi ghi report: dọn file mới và cho phép thử lại an toàn. Fixture tổng hợp và mock mạng được ghi rõ; các file sửa thử chỉ ở thư mục tạm, không sửa snapshot thật.

Lệnh trực tiếp `python -m unittest discover -s tests/data -v` cần biến `TV1_DATASET_VERSION` cho test artifacts/handoff; không đặt sẽ skip rõ ràng, không được tính nghiệm thu đủ. Runner thiết lập biến này và lưu UTF-8 log/summary, Python/dependencies, hash source và artifacts ở `logs/audit/tv1_tests_<run_id>/`.

Window/split/scaler một/năm bước thuộc TV2, chưa có trong suite TV1. Thành công trên máy hiện tại không chứng minh đã chạy trên máy thành viên khác. Xem notebook mục 9 và `reports/audits/TV1_Test_Summary.md`.
