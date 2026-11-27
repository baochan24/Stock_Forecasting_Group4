# Kiểm tra dự kiến: models

Mục5: dùng `.venv/tv3_clean/Scripts/python.exe -X utf8 scripts/run_tv3_checks.py --require-clean`. 89/89 tests đạt cả workspace và bản source độc lập, không fail/error/skip; user-site false, module imports trong venv, lock68 versions khớp, CPU build và pip check đạt. Runner lưu freeze/pip-check/origins/lock hash/source hashes. Dùng cùng venv chạy notebook03 để strict assertions đạt; venv audit cũ dưới đây là lịch sử. Docs/TV3_Setup_and_Reproduce.md và reports/audits/TV3_Environment_Reproduce.md có hướng dẫn/evidence; chưa xác nhận máy khác.

Mục4 TV3: **89 tests**, thêm12 trace_acceptance cases cho update/disk reload/JSON/preserved grads/schema/recurrence/state mismatch và child-mode guards. Float64 trace rtol1e-10/atol1e-12. CLI check_tv3_trace.py kiểm2 inputs TV2 thật×3 stages, không huấn luyện chính thức. Notebook TV3 hiển thị89 tests và trace evidence, xem TV3_Progress.md. Các số tests/tolerance dưới đây là lịch sử.

Mục3 TV3: **77/77 tests đạt**; thêm11 acceptance cases tại `test_lstm_acceptance.py` kiểm exact architecture/manual forward, numerical gradcheck tiny hidden2/T3 trên input/parameters, real temporary state_dict save/load sau Adam, eval/order/B1, wrong-horizon load rejection và storage/weight independence. Không training AAPL hoặc checkpoint chính thức. Evidence logs/audit/tv3_tests_20261123T023117585067Z. Runner/môi trường chưa lock sạch; số tests thấp hơn dưới đây là lịch sử.

Precision hiện tại23/11/2026: **66/66 tests đạt** với model/tensor fixture float64 explicit, thêm kiểm default parameters64 không đổi torch default dtype và từ chối float32 khi weights64. Adapter tests kiểm X/y tensor bằng mảngTV2 tuyệt đối, inverse rtol/atol1e-12; runner evidence logs/audit/tv3_tests_20261123T022146167444Z. State_dict/trace/gradient/Adam smoke đều chạy float64; logs và số tests trước bên dưới là lịch sử.

TV3 mục2: hiện **63/63 tests đạt**. Fixture test_tv2_sample_format cũ đã thay bằng output module TV2 chính thức; conftest.py sinh dữ liệu tổng hợp, test_lstm_tv2_adapter.py thêm8 cases (param 1/5) về identity/precision/no-refit/copy/input-only và lỗi schema/pairing. Chạy runner cũ; evidence logs/audit/tv3_tests_20261123T021104308840Z.

CLI `scripts/check_tv3_tv2.py --dataset-version <version> --scaler-dir <folder> --prepared-dir <folder>` chạy bằng venv tv3_review_env, kiểm nguồn và toàn bộ batch thật trước adapter/model forward. Snapshot đã chốt5460 samples đều đạt, source/artifacts không đổi, xem TV3_Progress.md mục2. Không cần artifacts thật cho unit tests. Vẫn chưa khóa môi trường sạch hoặc train model; ghi chú55 tests bên dưới là lịch sử mục1.

Shape, forward và inference độc lập; truy vết đối chiếu.

TV3 mục 1 (23/11/2026): đã tiếp nhận 4 file test_lstm_one_step.py, test_lstm_multi_step.py, test_lstm_contract.py, test_lstm_trace.py từ commit `1f209b70c5690fb5e41b3b26d8eab36b2b6c029d`, giữ nguyên source. Chạy trên workspace đúng layout: **55/55 test đạt**, không fail/error/skip.

Lệnh từ gốc workspace: `.venv/tv3_review_env/Scripts/python.exe -X utf8 scripts/run_tv3_checks.py`. Runner gọi pytest tests/models, lưu pytest.log/junit.xml/summary.json và source hashes/environment ở logs/audit/tv3_tests_<run_id>; fail khi test lỗi/skip hoặc source thay đổi trong lúc chạy. OMP/MKL threads=1 để kiểm thử CPU ổn định tài nguyên, không phải đo benchmark.

Môi trường audit hiện có Python3.13.7, torch2.14.1+cpu, pytest9.2.0, numpy2.4.4, kế thừa site packages; chưa lock sạch, mục 5 còn chờ. `python -m pytest tests/models -v` cũng chạy trực tiếp nếu đã có dependencies, không cần sửa PYTHONPATH/import tới bản copy khác.

Tests hiện gồm shape/finite/parameter counts, h/c zero mới/window independence, gradient/optimizer smoke/state_dict roundtrip và trace/read-only/mismatch. `test_tv2_sample_format` vẫn là fixture schema PR cũ, chưa chứng minh tích hợp TV2 hiện tại; sẽ xử lý ở mục 2. Tensor ngẫu nhiên là fixture, không phải kết quả dự báo/huấn luyện chính thức.
