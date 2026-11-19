# scripts

Entry points nghiên cứu/train/evaluate/release sau khi triển khai; không tạo script giả chạy được.

## Công cụ notebook khám phá dữ liệu

- `audit_tv1_completion.py --dataset-version <version>`: kiểm tra lại 10 hạng mục và dữ liệu, dùng tests/provenance/quality/output/handoff/reproduction evidence; chưa tự xác nhận người nhận độc lập. Tạo audit mới dưới `data/metadata/tv1_final_audit_<run_id>/`.

- `check_tv1_reproducibility.py --python <clean-python> --dataset-version <version>`: bản source riêng + dữ liệu từ ZIP, pip check/freeze, tests/notebook và bằng chứng cùng máy. Xem `docs/TV1_Setup_and_Reproduce.md`; không thay xác nhận người nhận độc lập.

- `run_tv1_checks.py --dataset-version <version>`: chạy suite TV1 trên artifacts được chỉ định, lưu log/summary/source hashes theo run ID và exit code nghiệm thu; xem `tests/data/README.md`.

- `package_tv1_snapshot.py --dataset-version <version> --complete`: yêu cầu đủ raw/validated/metadata/validation report, kiểm tra liên kết hash và tạo receipt `_complete.json` riêng, giữ gói raw cũ.
- `verify_tv1_handoff.py --archive <zip> --checksum <zip.sha256>`: kiểm tra gói đầy đủ bằng Python chuẩn; không giải nén, không mạng, không sửa dữ liệu.

- `package_tv1_snapshot.py --dataset-version <version>`: chuẩn bị ZIP raw/metadata, manifest và checksum tại `artifacts/releases/`; receipt ở `data/metadata/`. Gói raw-only không phải model release. Không tải lại, không ghi đè receipt, không chia sẻ tự động; cần validation và nơi nhận để hoàn tất bàn giao.

- `build_data_exploration.py`: tạo `notebooks/01_AAPL_Data_Exploration.ipynb`; chạy lại sẽ xóa output notebook hiện có.
- `execute_data_exploration.py`: chạy notebook và lưu bảng/biểu đồ vào output; dùng môi trường `.venv/eda` và kernel cục bộ đúng Python.

Chạy từ gốc repo: `.venv/eda/Scripts/python.exe scripts/build_data_exploration.py` hoặc `python scripts/execute_data_exploration.py`. Xem `notebooks/README.md` và `notebooks/requirements-eda.txt` về cách tạo môi trường, dependencies và nguồn snapshot. Code download/validation TV1 nằm ở `backend/data/`; các script ở đây chỉ điều phối notebook.
