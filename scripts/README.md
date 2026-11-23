# scripts

TV3 mục6: `package_tv3_handoff.py` tạo ZIP source/contracts/tests/lock/notebook và artifacts TV1/TV2 cần verify (không trained weights), checksum/manifest ID mới. `verify_tv3_handoff.py` chạy từ gốc giải nén, kiểm file hashes/notebook cell sources, tests --require-clean và integration/trace. Notebook outputs được phép cập nhật; code cells không được sửa âm thầm. Dùng venv tv3_clean; xem docs/TV3_Handoff_TV4_TV6.md và reports/audits/TV3_Final_Handoff.md. Không upload/push tự động.

TV3 mục5: `requirements-tv3-lock.txt` ghim68 dependencies Windows/Python3.13.7 CPU; `run_tv3_checks.py --require-clean` bắt buộc isolation/origins/lock/CPU/pip-check/tests. `check_tv3_reproducibility.py` copy source/artifacts sang thư mục mới, chạy tests/integration/trace trong copy và kiểm hashes hai bên; không tải lại data hoặc training. Chạy bằng `.venv/tv3_clean/Scripts/python.exe -X utf8`. Notebook03 hiện cũng dùng venv này. Báo cáo TV3_Environment_Reproduce.md, setup docs/TV3_Setup_and_Reproduce.md; máy khác còn chờ.

TV3 mục4: `check_tv3_trace.py --dataset-version <version> --scaler-dir <folder> --prepared-dir <folder>` ghi6 trace JSON có envelope identity/date và checksums, initial/synthetic-step/reload; chỉ2 representative train inputs, không training/metric hoặc checkpoint nghiên cứu. Dùng tv3_review_env; notebook TV3 gọi CLI này, biểu diễn gate/recurrence và lưu output. run_tv3_checks.py hiện89 tests.

Notebook từng TV: `build_member_notebooks.py --member 2/3/all [--overwrite]` sinh notebook từ cells gọi backend; mặc định không ghi đè. `execute_member_notebooks.py --member 2/3/all` chạy bằng interpreter hiện tại (dùng tv3_review_env đã có notebook tools), local kernelspec rõ ràng và outputs lưu vào notebooks/, evidence logs/audit/member_notebooks_<run>. Chỉ regenerate khi cập nhật builder, vì xóa outputs cũ; xem notebooks/README.md.

TV3 mục3: run_tv3_checks.py hiện77 tests, gồm11 acceptance cases architecture/manual forward/numerical gradients/disk roundtrip/independent weights. Runner giữ pytest log/JUnit/source hashes; chưa thay training loop TV4. Evidence và giới hạn tại reports/audits/TV3_Progress.md.

TV3 precision hiện tại: check_tv3_tv2.py dùng CPU float64, không downcast, tensor-copy difference=0/inverse rtol=atol1e-12. run_tv3_checks.py hiện66 tests. `benchmark_tv3_precision.py` đo chi phí CPU float32/64 trên tensor tổng hợp, model copies riêng, không training chính thức/tuning; lưu logs/audit/tv3_precision_<run>. Xem TV3_Progress.md cho số đo/giới hạn. Mô tả float32 cũ phía dưới là lịch sử.

TV3 mục2: `check_tv3_tv2.py --dataset-version <version> --scaler-dir <folder> --prepared-dir <folder>` chạy venv tv3_review_env, accept TV1/scaler/prepared, audit hợp đồng, cast float32 và forward CPU toàn bộ samples với trọng số khởi tạo; không fit/optimizer/metric. Lưu logs/audit/tv3_tv2_<run>/summary.json có hashes/precision/shape/identity. Runner run_tv3_checks.py hiện63 tests và ghi thêm source hashes adapter/conftest.

## TV3 — tests bố trí module mục 1

`run_tv3_checks.py` chạy pytest models từ gốc project, giữ pytest.log/junit.xml/summary.json và source hashes ở logs/audit/tv3_tests_<run_id>. Dùng `.venv/tv3_review_env/Scripts/python.exe -X utf8 scripts/run_tv3_checks.py` hiện có dependencies audit; chưa là môi trường sạch/lock chính thức. Không cần snapshot/model training để chạy55 tests nền. Adapter TV2 chính thức chờ mục2.

## TV2 — bàn giao và tái lập mục 10

- `requirements-tv2-lock.txt`: bộ 15 dependencies đủ cho TV2 + tiếp nhận TV1, không gồm notebook/model.
- `run_tv2_checks.py`: tất cả tests TV2, lưu log/summary/environment/freeze/source hashes.
- `package_tv2_handoff.py --dataset-version <version> --scaler-dir <folder>`: source+snapshot+scaler+prepared ZIP/checksum mới, không upload.
- `verify_tv2_handoff.py`: chạy trong gốc gói giải nén, kiểm mọi checksum, accept snapshot/scaler/prepared, audit và rebuild exact, không fit.

Chạy bằng venv sạch `.venv/tv2_clean/Scripts/python.exe -X utf8`. Hướng dẫn chi tiết docs/TV2_Setup_and_Handoff.md; kết quả reports/audits/TV2_Final_Handoff.md. Không cần train để kiểm tra.

## TV2 — audit leakage mục 9

`audit_tv2_leakage.py --dataset-version <version> --scaler-dir <folder>` chạy bằng `.venv/tv2/Scripts/python.exe -X utf8`, đối chiếu train moments/temporal coverage độc lập, contract và perturbations hai mode, ghi `logs/audit/tv2_leakage_<run_id>/summary.json` gồm ví dụ ngày/giá đầy đủ. Cấm fit/partial_fit, không sửa artifacts thật và không chạy model/metric. Không thay cho audit training/consumer trong giai đoạn sau.

## TV2 — hợp đồng input/target mục 8

`check_tv2_contracts.py --dataset-version <version> --scaler-dir <folder>` kiểm tra hai mode so snapshot/scaler đã accept, IDs duy nhất giữa modes, adapter input-only tạo X khớp batch; cấm fit/partial_fit, kiểm tra hashes không đổi. Chạy `.venv/tv2/Scripts/python.exe -X utf8`, lưu `logs/audit/tv2_contracts_<run_id>`. Không huấn luyện hoặc xây API.

## TV2 — mở rộng audit cửa sổ 5 bước (mục 7)

`check_tv2_one_step.py --forecast-length 5 --dataset-version <version> --scaler-dir <folder>` kiểm tra tất cả cửa sổ 5 bước, cả 5 target cùng split, inverse X/y, shapes/exclusion counts và hashes không đổi; ghi logs/audit/tv2_five_step_<run_id>. Giữ tên script, mặc định forecast-length=1 để tương thích lệnh một bước. Không train/model metric.

## TV2 — windowing một bước mục 6

`check_tv2_one_step.py --dataset-version <version> --scaler-dir <folder>` kiểm tra mọi cửa sổ một bước trên snapshot đã accept, so ngày/giá/origin/indices/shapes, cấm refit; tạo evidence mới `logs/audit/tv2_one_step_<run_id>`. Chạy bằng `.venv/tv2/Scripts/python.exe -X utf8`. Không training hoặc tạo cửa sổ 5 bước.

## TV2 — kiểm chứng scale/inverse mục 5

`check_tv2_scaling.py --dataset-version <version> --scaler-dir <folder>` xác minh snapshot/scaler lưu sẵn, kiểm tra shape/roundtrip với fit/partial_fit bị cấm; lưu evidence mới trong logs/audit/tv2_scaling_<run_id>. Chạy bằng `.venv/tv2/Scripts/python.exe -X utf8`. Không tạo scaler/windows.

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
