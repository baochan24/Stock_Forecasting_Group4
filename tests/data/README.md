# Kiểm tra dự kiến: data

Kiểm tra window/split/scaler/ngày, ví dụ bằng tay một/năm bước.

## TV1 — bộ kiểm thử thực thi

Chạy từ gốc repo bằng `.venv/eda/Scripts/python.exe scripts/run_tv1_checks.py --dataset-version <version>`. Cần đủ raw/metadata/validated/validation report và receipt `_complete.json` trỏ gói ZIP của version đó. Lệnh trả exit code khác 0 nếu fail/error/skip hoặc 4 artifacts nguồn thay đổi.

Suite TV1 hiện gồm 34 test methods (có nhiều subcase): pipeline cơ bản/artifacts thật 4; quality 7; provenance 4; versioning 5; standard output 4; handoff integrity 6; pipeline tích hợp offline 4. Audit cuối bổ sung hồi quy lỗi ghi report: dọn file mới và cho phép thử lại an toàn. Fixture tổng hợp và mock mạng được ghi rõ; các file sửa thử chỉ ở thư mục tạm, không sửa snapshot thật.

Lệnh trực tiếp `python -m unittest discover -s tests/data -v` cần biến `TV1_DATASET_VERSION` cho test artifacts/handoff; không đặt sẽ skip rõ ràng, không được tính nghiệm thu đủ. Runner thiết lập biến này và lưu UTF-8 log/summary, Python/dependencies, hash source và artifacts ở `logs/audit/tv1_tests_<run_id>/`.

Window/split/scaler một/năm bước thuộc TV2, chưa có trong suite TV1. Thành công trên máy hiện tại không chứng minh đã chạy trên máy thành viên khác. Xem notebook mục 9 và `reports/audits/TV1_Test_Summary.md`.

## TV2 — kiểm tra phần code tiếp nhận

Mục 10: **51 test methods**, thêm 5 `test_tv2_prepared_artifacts.py` (roundtrip/contract hai modes, checksum corruption, sai identity, path member injection, không ghi đè). Runner `scripts/run_tv2_checks.py` lưu log thật/summary/freeze/source hashes, fail khi fail/error/skip. Đã chạy venv sạch và source gói giải nén độc lập: 51/51 cả hai. Xem reports/audits/TV2_Final_Handoff.md; chưa nghiệm thu máy khác. Các tổng phía dưới là lịch sử.

Mục 9: hiện **46 test methods**, thêm 5 `test_tv2_leakage_audit.py`. Kiểm tra oracle độc lập bắt thiếu mẫu dù xóa đồng bộ, scaler fit toàn dataset, input tương lai, exclusions/fit metadata sai và nguồn đảo. CLI audit_tv2_leakage.py kiểm tra mọi mẫu thật, train moments và perturbation 2023/2024 không đổi input trước cutoff. Không coi fixture hoặc audit preprocessing là chứng nhận model không tuning test.

Mục 8: **41 test methods**, thêm 5 `test_tv2_contracts.py`, gồm nhiều subcases sửa hỏng ID/version/ngày/shape/horizon/pairing và kiểm tra adapter không cần targets/y, chống target injection. CLI check_tv2_contracts.py kiểm tra toàn bộ 5460 mẫu/IDs hai mode trên snapshot thật; không thay thế audit leakage mục 9 hoặc consumer model test.

Mục 7: tổng **36 test methods**, thêm 4 trong `test_tv2_five_step_windows.py`, đồng thời chạy lại tests one-step sau khi ghép lõi chung. Kiểm tra targets31..35 bằng tay, 5 target cùng tập, ranh giới/exclusion, no refit/input không chứa tương lai, ID f1/f5 riêng và empty shapes. CLI `check_tv2_one_step.py --forecast-length 5 ...` đối chiếu mọi mẫu thật/inverse/hash; không huấn luyện hoặc metric test.

Mục 6 (22/11/2026): hiện **32 test methods**, thêm 4 `test_tv2_one_step_windows.py`: đối chiếu input1..30→target31, ngày/origin/shape/inverse, ranh giới/unique IDs, thay giá tương lai không đổi input cũ hoặc refit, thiếu lịch sử/empty shapes/copy isolation. CLI `scripts/check_tv2_one_step.py` kiểm tra tất cả raw windows trên snapshot đã accept. Bộ tests này chưa chứng nhận multi-step hoặc consumer inference/training.

Mục 5 (21/11/2026): hiện 28 test methods, thêm 5 trong `test_tv2_saved_scaling.py`. Kiểm tra shapes sau save/load, công thức, dung sai float64 1e-12, không refit/sửa input/state, view readonly/noncontiguous và scaler hằng. CLI `scripts/check_tv2_scaling.py --dataset-version <version> --scaler-dir <folder>` kiểm tra 12 trường hợp theo split trên snapshot thật; mảng reshape chưa phải cửa sổ dự báo.

Mục 4: tổng **23 test methods**, thêm 6 train_scaler tests. Môi trường `.venv/tv2` chạy toàn suite và CLI thật có sklearn/calendar trong cùng môi trường phát triển. Test train-only spy số lần fit, thay val/test không đổi tham số, nạp/transform cấm fit, roundtrip, mismatch/corruption và không ghi đè ID. Đầu vào snapshot được mock trong train_scaler unit tests; CLI thật gọi acceptance TV1, không mock.

Sau mục 3: tổng 17 test methods, thêm 5 temporal split tests trong `test_tv2_temporal_split.py`. Chạy cùng glob `test_tv2*.py` như dưới. CLI snapshot thật `scripts/inspect_tv2_split.py --dataset-version <version>` kiểm tra kế hoạch split/historical context; số phiên chưa phải số mẫu window. Tests snapshot vẫn dùng mock fresh quality, CLI dùng kiểm tra TV1 thật.

Chạy cả suite TV2: `python -X utf8 -m unittest discover -s tests/data -p 'test_tv2*.py' -v`. Hiện 12 test methods, gồm 6 module nền và 6 snapshot. Fixture snapshot tổng hợp 3 phiên, chỉ mock fresh calendar quality vì không phải lịch đầy đủ 11 năm; provenance/hash/schema vẫn kiểm tra thực. Kiểm chứng snapshot thật không mock dùng `scripts/inspect_tv2_input.py` trong môi trường có exchange_calendars. Windows sandbox có thể cần quyền chạy fixture trong thư mục tạm; không thay artifacts thật.

`python -m unittest discover -s tests/data -p test_tv2_imported_code.py -v` hiện có 6 test methods: train scaler không đổi sau transform dữ liệu tương lai tổng hợp, roundtrip các shape model, train array không hợp lệ, transform/scaler không hợp lệ, split giữ liên kết ngày/giá và dataset không hợp lệ. Các test chưa bao gồm windowing, xác minh snapshot, lưu/nạp scaler hoặc tích hợp và không được dùng để chốt toàn bộ TV2. Môi trường cần numpy/pandas/scikit-learn; không yêu cầu cài thêm vào môi trường TV1.
