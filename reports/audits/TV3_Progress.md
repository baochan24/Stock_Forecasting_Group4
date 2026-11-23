# TV3 — tiến độ và nghiệm thu từng hạng mục

## Mục6 — source/contract handoff đạt kỹ thuật local

23/11/2026: đã hoàn thiện docs/TV3_Handoff_TV4_TV6.md và persistence helper lstm_checkpoint.py; loader CPU float64 kiểm identity/hash/horizon/lookback, actual state dtype và mặc định từ chối trained=False.10 tests mới đạt, toàn suite99/99 strict-clean. Gói cuối TV3_Handoff_20261123T032109345167Z.zip đã giải nén và verify tests/integration5460 samples/trace6 stages đạt; SHA256 bf121e8f1f07ef2860f35b67471260abb5037ad8e4be7bf03683899958964307. Notebook mục6 hiển thị checksum/receipt/configs và trạng thái chưa trained/nhận bàn giao. Chi tiết reports/audits/TV3_Final_Handoff.md, evidence logs/audit/tv3_handoff_repro_20261123T032140745602Z.

**TV3 mục1–6 sẵn sàng kỹ thuật local.** Chưa xác nhận máy người nhận/TV4-TV6 đã nhận, chưa có checkpoint AAPL chính thức hoặc phê duyệt API trace. Mục6 đạt chuẩn bị/kiểm bàn giao local, nghiệm thu phối hợp còn chờ; không train thay TV4 hoặc tự upload/push/merge. Các trạng thái chờ trong phần lịch sử dưới đây không thay kết luận mới nhất.

Notebook03 sau mục6 **22 cells/13 code,13/13 chạy đạt**, kiểm đúng ZIP/receipt cuối, source và outputs lưu local. Evidence `logs/audit/member_notebooks_20261123T032341382654Z/summary.json`; không error outputs. Chưa push hoặc thay gói TV2 đã chốt.

## Mục5 — môi trường CPU sạch và tái lập local đã đạt

23/11/2026: theo yêu cầu tiếp tục và luôn ghi báo cáo, đã khóa68 dependencies và tạo tv3_clean không system/user site. **89/89 tests đạt** với --require-clean,0 versions lệch lock, CPU torch build, pip check exit0. Source/artifact copy độc lập cũng chạy tests/integration5460 mẫu/trace6 stages đạt; notebook21 cells/12 code chạy12/12 bằng kernel sạch. Kernel VS Code AAPL Coursework CPU float64 đã đăng ký. Không train/metric/chọn model trên test.

Chi tiết lệnh/bằng chứng/giới hạn: `reports/audits/TV3_Environment_Reproduce.md`, setup `docs/TV3_Setup_and_Reproduce.md`. Evidence tests `logs/audit/tv3_tests_20261123T030530643561Z/summary.json`; độc lập `logs/audit/tv3_repro_20261123T030500403955Z/summary.json`; notebook `logs/audit/member_notebooks_20261123T030454864977Z/summary.json`. Lock SHA256 b3c2b51dee9b06fc7399fbc81635530d38bcde77abbb1f68732f7520ec204648. **Mục5 đạt local, chờ xác nhận máy khác; mục6 chưa làm.** Không thay môi trường TV1/TV2, không push/merge/Drive. Các ghi nhận môi trường kế thừa phía dưới là lịch sử trước mục5.

## Mục4 — nghiệm thu trace local23/11/2026

Bổ sung tests/models/test_lstm_trace_acceptance.py: **12 ca mới** qua hai mode, gồm trace trước/sau Adam tổng hợp và file state_dict/JSON roundtrip; giữ nguyên weights/gradients đã có/input/mode; schema/shape/first-step recurrence; cố ý làm sai hidden/cell reference phải báo lỗi; parent eval nhưng child train cũng bị từ chối. Không training AAPL hoặc tạo checkpoint chính thức.

Trace float64 dùng rtol1e-10/atol1e-12 thay dung sai32 cũ (fallback32 vẫn1e-5/1e-6); không đổi fields của core schema hoặc công thức. docs/TV3_Trace_Contract.md mô tả điều kiện/schema/giới hạn nội bộ, chưa tuyên bố API TV6 đã duyệt.

Runner: **89/89 tests đạt, 0 fail/error/skip**, evidence `logs/audit/tv3_tests_20261123T024756960446Z/summary.json`, pytest.log và junit.xml. CLI check_tv3_trace.py trên hai representative train inputs TV2 thật: **6/6 stage checks đạt**, trace after_reload bằng after_synthetic_step tuyệt đối, JSON roundtrip không đổi. Max hidden/cell abs error **5.551115123125783e-17**; max prediction abs error **1.3877787807814457e-17**. Evidence `logs/audit/tv3_trace_20261123T024913981785Z/summary.json` và6 trace JSON có checksum. No-fit/scaler, source artifacts hashes không đổi, trace không sửa input/weights/gradient/mode. Update là1 Adam step với synthetic_x/target0, không là model học dự báo.

Notebook TV3 được bổ sung mục4 gọi CLI thật, bảng6 stages và30 phiên gate/hidden/cell kênh0 cùng biểu đồ, kiểm recurrence30×32; ghi rõ không diễn giải kinh tế/gate hook. Cập nhật builder và thực thi notebook, không chép output giả. Mục5/6 vẫn chờ; chưa push/merge/Drive hoặc sửa TV1/TV2 artifacts.

Notebook03 sau cập nhật **19 cells/11 code,11/11 code chạy đạt**, không error outputs; evidence `logs/audit/member_notebooks_20261123T025007872981Z/summary.json`. Bảng test/JUnit được chạy mới trong notebook và hiển thị đủ89 cases, phần trace gọi CLI tạo evidence mới trong cùng phiên thực thi.

## Notebook trình bày theo yêu cầu người dùng23/11/2026

Đã bổ sung `notebooks/03_TV3_LSTM_Development_and_Tests.ipynb`:15 cells/8 code, ghi quá trình mục1–3 và float64, chạy source/models/TV2 thật và suite tests, hiển thị đầy đủ từng testcase/JUnit và source hashes. Mục4–6 vẫn ghi chờ; có tests trace nền không coi là đã nghiệm thu mục4. Notebook gọi backend/scripts, không training hoặc tạo kết quả dự báo giả. Môi trường chạy vẫn là tv3_review_env kế thừa site packages, không tự chốt mục5.

TV2 có notebook riêng02_TV2_Preprocessing_and_Audit.ipynb gồm25 cells/13 code. TV1 giữ nguyên. Builder/executor nằm trong scripts/build_member_notebooks.py và execute_member_notebooks.py; kết quả chạy cả hai lúc đầu `logs/audit/member_notebooks_20261123T024215819099Z/summary.json`. TV3 được cập nhật tiếp để bảng hiển thị đủ77 tests (không bị pandas rút gọn). Xem notebooks/README.md cho thao tác và cập nhật sau mỗi mục.

Bản TV3 sau chỉnh hiển thị77 testcase đã chạy lại8/8 code cells, không lỗi; evidence `logs/audit/member_notebooks_20261123T024407751523Z/summary.json`. Cả hai notebook đã lưu outputs và schema nbformat hợp lệ, không ghi pass bằng tay. Chưa push/Drive.

## Cập nhật precision theo yêu cầu người dùng — 23/11/2026

Người dùng đề nghị giữ float64 thay vì hạ float32 và yêu cầu thử triển khai. Đã đổi LSTM/Linear mặc định cả hai mode sang float64 explicit, adapter sao chép CPU float64 bằng đúng mảng TV2; không đổi global torch default dtype, không sửa snapshot/scaler/prepared hoặc shape. Tests tạo tensor đúng dtype; guard từ chối float32 với model mặc định. Model vẫn có thể dùng .float() trong benchmark riêng, không phải đường mặc định.

`scripts/run_tv3_checks.py`: **66/66 đạt**, không fail/error/skip; evidence `logs/audit/tv3_tests_20261123T022146167444Z/summary.json`. Đã kiểm gradient/Adam smoke/state_dict/trace và bổ sung bảo đảm parameters mặc định float64 không thay global dtype. Các logs55/63 và mô tả float32 bên dưới giữ lịch sử.

`scripts/check_tv3_tv2.py` float64: **5460 mẫu thật đạt**, X/y tensor bằng mảng float64 nguồn tuyệt đối (max difference0); inverse target max abs error **5.684341886080802e-14 USD**, rtol=atol=1e-12. Input-only khớp training X, IDs/order giữ nguyên, no-fit/no-grad/model state/scaler/artifacts hashes không đổi. Evidence `logs/audit/tv3_tv2_20261123T022312497066Z/summary.json`. Model trọng số khởi tạo, không đánh giá forecasting/tuning trên test.

Benchmark tổng hợp `scripts/benchmark_tv3_precision.py`, evidence `logs/audit/tv3_precision_20261123T022251223682Z/summary.json`: CPU1 thread, B32,T30, warmup3,5 rounds×10 iterations, thứ tự dtype luân phiên, cùng base weights/input. Chỉ cập nhật model copies với target tổng hợp, không training AAPL hoặc lưu checkpoint phục vụ project.

| Model | Forward float32/64 (ms/batch) | Adam step float32/64 (ms/batch) | Weights bytes float32/64 |
|---|---|---|---|
| 1 bước | 0.548 / 2.369 | 3.837 / 11.292 | 18052 / 36104 |
| 5 bước | 0.593 / 2.054 | 3.614 / 11.303 | 18580 / 37160 |

Lưu/nạp float64 cho output bằng nhau tuyệt đối; trace float64 đạt, max hidden/cell khoảng5.55e-17. Đây là microbenchmark máy hiện tại, phụ thuộc CPU/backend/threads/tải máy; không suy thành thời gian training chính thức. Weights/input numeric storage gấp2 (không phải toàn bộ RAM process); chưa tính activations/gradients/Adam buffers. Float64 không bảo đảm dự báo tốt hơn, nhưng đã đáp ứng lựa chọn precision nhất quán của người dùng. Không có checkpoint chính thức cần migrate; khi TV4 triển khai phải tạo model/tensors/optimizer state phù hợp dtype và ghi cấu hình.

Mục1–2 vẫn hoàn thành local theo dtype mới; chưa tự chốt mục3–6. Chưa push/merge/Drive, không sửa môi trường TV1/TV2 hoặc notebook. Bước tiếp theo vẫn mục3 nghiệm thu model riêng.

## Flow giữ theo yêu cầu người dùng

| Mục | Công việc | Trạng thái |
|---|---|---|
| 1 | Đặt source đúng module, public imports và chạy lại tests | **Hoàn thành local 23/11/2026** |
| 2 | Tích hợp batch TV2 chính thức và adapter dtype | **Hoàn thành local 23/11/2026** |
| 3 | Nghiệm thu hai model/forward/state/gradient/lưu-nạp | **Hoàn thành local 23/11/2026, float64** |
| 4 | Nghiệm thu trace với model lưu/nạp và cập nhật trọng số | **Hoàn thành local 23/11/2026** |
| 5 | Khóa môi trường CPU, hướng dẫn/logs tái lập sạch | **Đạt local23/11/2026; chờ xác nhận máy khác** |
| 6 | Tài liệu, bàn giao TV4/TV6 và phối hợp checkpoint | **Đạt chuẩn bị/verify local; chờ người nhận và checkpoint chính thức** |

## Mục 1 — tiếp nhận và bố trí đúng source

Các kết quả mục1–2 bên dưới giữ lịch sử; dtype mới nhất là float64 như phần precision phía trên và nghiệm thu mục3 phía dưới.

Nguồn nhánh Thien-code137-patch-1, commit `1f209b70c5690fb5e41b3b26d8eab36b2b6c029d`. Theo yêu cầu người dùng bắt đầu hoàn thiện từng mục, đã tiếp nhận **10 file Python** nguyên byte vào workspace:

- backend/models/lstm_one_step/model.py và __init__.py.
- backend/models/lstm_multi_step/model.py và __init__.py.
- backend/model_trace/lstm_trace.py và __init__.py.
- tests/models/test_lstm_one_step.py, test_lstm_multi_step.py, test_lstm_contract.py, test_lstm_trace.py.

Không thêm các thư mục source top-level sai layout, không sửa thuật toán/trace/tests của tác giả. Không di chuyển hoặc xóa file sẵn có trong workspace, không sửa checkout nhánh gốc hoặc remote. README module vẫn giữ trách nhiệm, cập nhật trạng thái local thay vì chép tuyên bố tests tích hợp cũ của tác giả.

Public imports chạy từ gốc project qua backend.models.lstm_one_step, backend.models.lstm_multi_step và backend.model_trace. Không cần sys.path tới bản chẩn đoán. Thêm scripts/run_tv3_checks.py để ghi evidence thực chạy; không test stub hoặc output giả.

Lệnh `.venv/tv3_review_env/Scripts/python.exe -X utf8 scripts/run_tv3_checks.py`: **55 tests, 0 failures, 0 errors, 0 skipped, passed**. Evidence `logs/audit/tv3_tests_20261123T020457014778Z/summary.json`, pytest.log và junit.xml; summary ghi hashes10 source/tests và source_unchanged=true, môi trường và CPU thread settings. Môi trường Python3.13.7/torch2.14.1+cpu/pytest9.2.0/numpy2.4.4 là venv audit kế thừa site packages, không gọi là sạch hoặc tái lập máy khác. Tests là tensor tổng hợp, không phải huấn luyện chính thức.

Audit trước đã chứng minh nguyên nhánh lỗi collection4 files, bản sửa layout chẩn đoán55 pass; nay workspace thực đã đạt55, không còn cần layout probe. Không thay lịch sử kết quả nhánh gốc; chi tiết xem TV3_Thien_Branch_Audit_20261123.md.

Giới hạn và bước tiếp theo: chưa sửa fixture test_tv2_sample_format cũ, chưa có adapter float64→float32 của consumer TV2, chưa tạo checkpoint/training/model metrics. Mục2 sẽ xử lý input TV2 hiện tại có version/hash, không nhân bản preprocessing/scaler hoặc tự làm training loop TV4. Chưa push/merge/Drive hoặc thay notebook TV1 trong mục1.

## Mục 2 — tích hợp chính thức TV2 và tensor float32

Đã thêm `backend/data/preparation/tensors.py` (phần adapter tùy chọn cần torch, không đổi dependencies/môi trường TV2). `make_lstm_inputs(inputs, scaler, dataset_version=..., forecast_length=...)` chỉ nhận Forecast Input records, kiểm tra identity/schema bằng module TV2 rồi tạo X CPU float32 độc lập. Không có y/target trong interface. `make_lstm_training_batch(batch, scaler, ...)` kiểm tra count/shape/dtype float64 TV2, pairing ID/order/dates/split/horizon, raw/scaled values rồi trả X/y CPU float32 cùng bản sao metadata. Không fit/scaler mới/loss/optimizer/model logic trong adapter; source snapshot/scaler phải được accept trước.

Không đổi kiến trúc/forward LSTM hoặc artifact TV2. Thay fixture schema PR#2 trong test_lstm_contract.py bằng dữ liệu từ module windowing TV2 chính thức (fixture tổng hợp để unit tests không phụ thuộc artifacts). Thêm conftest.py và test_lstm_tv2_adapter.py: no refit, precision/copy isolation, input-only chạy không có targets/y, target injection/mixed mode/wrong version/pairing/scaled values/dates/horizon bị từ chối. Runner lưu hashes cả adapter và fixture/tests mới.

Suite `.venv/tv3_review_env/Scripts/python.exe -X utf8 scripts/run_tv3_checks.py`: **63/63 đạt, 0 fail/error/skip**. Evidence `logs/audit/tv3_tests_20261123T021104308840Z/summary.json` và pytest.log/junit.xml. Model/trace code gốc vẫn giữ nguyên; tests tích hợp được nâng cấp theo TV2 thực.

CLI `.venv/tv3_review_env/Scripts/python.exe -X utf8 scripts/check_tv3_tv2.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z --prepared-dir data/prepared/tv2_prepared_20261122T145943242978Z`: **passed**, forward toàn bộ **5460 mẫu**, gồm 1 bước1984/250/502 và 5 bước1980/246/498. Load nguồn có acceptance/hash, load prepared/scaler identity, audit train moments/coverage/contracts trước adapter. Input-only X khớp training X tuyệt đối, IDs/order giữ nguyên, forward CPU float32 ra (B,1)/(B,5) hữu hạn, inverse output hữu hạn. Cấm StandardScaler.fit/partial_fit; model state/gradient/scaler state và hashes mọi file snapshot/scaler/prepared không đổi. Evidence `logs/audit/tv3_tv2_20261123T021236520014Z/summary.json` gồm checks từng split/mode, source/artifact hashes và môi trường.

Dung sai cast: rtol1e-6/atol1e-7 ở thang chuẩn hóa. Kiểm tra y float32 inverse về raw USD dùng rtol1e-6/atol1e-4; max abs error thực đo **1.028289665327975e-05 USD**, max abs X scaled cast **2.1163697727644148e-07**. Đây là sai số số học cast, không phải MAE/RMSE dự báo; không thay dung sai float64 TV2 cũ. Model dùng trọng số ngẫu nhiên seed42 để smoke test, không checkpoint huấn luyện, không chọn seed/model bằng test. Không train hoặc tính metric dự báo trên phân đoạn test.

Giới hạn: venv audit kế thừa site packages, chưa lock sạch/máy khác (mục5). Adapter chưa phải inference/API TV6 hoặc training loop TV4. Mục3 tiếp tục nghiệm thu riêng kiến trúc/state/gradient/lưu-nạp; mục4 trace. Chưa push/merge/Drive hoặc thay notebook TV1 trong mục2.

## Mục 3 — nghiệm thu hai model float64

Không đổi model/adapter ở mục này; bổ sung `tests/models/test_lstm_acceptance.py`, gồm **11 ca nghiệm thu** (5 nhóm×2 mode và1 kiểm tra trọng số độc lập). Kiểm tra:

| Tiêu chí | Bằng chứng test | Kết quả |
|---|---|---|
| Đúng kiến trúc mặc định | 1 LSTM1 lớp, một chiều, input1/hidden32, batch_first, không projection; Linear ra1/5, đúng2 child modules | Đạt |
| Đúng forward | So model(x) với LSTM h/c zero→lấy time step cuối→Linear, output bằng nhau tuyệt đối; không sửa x | Đạt |
| Gradient số học | torch.autograd.gradcheck trên input và toàn bộ parameters của lõi shared forward với hidden2/T3, float64, fast_mode, eps1e-6/atol1e-5/rtol1e-3 | Đạt hai mode |
| Gradient default model | Suite có backward hidden32, gradient finite/không mất kết nối và dtype64; Adam/MSE synthetic cập nhật weights hữu hạn | Đạt |
| Không carry state giữa cửa sổ | Tests zero states mới, mẫu riêng/batch/đảo thứ tự khớp rtol/atol1e-12, batch cuối B1 đúng shape | Đạt |
| Eval không cập nhật | inference_mode, không gradient, không đổi parameters/buffers/mode | Đạt |
| Lưu/nạp sau cập nhật | Sau1 bước Adam tổng hợp, lưu state_dict vào file tạm thật, nạp weights_only/CPU/strict vào instance mới; parameters64 và predictions bằng nhau tuyệt đối | Đạt |
| Không nhầm horizon | strict load state_dict mode kia báo size mismatch | Đạt |
| Hai model độc lập | Parameter storage addresses rời nhau; cập nhật one-step không đổi weights multi-step | Đạt |

Lệnh `.venv/tv3_review_env/Scripts/python.exe -X utf8 scripts/run_tv3_checks.py`: **77/77 tests đạt, 0 fail/error/skip**. Evidence `logs/audit/tv3_tests_20261123T023117585067Z/summary.json`, pytest.log và junit.xml. Runner ghi hash source/tests và source_unchanged=true, Python/torch/pytest và CPU thread settings. Tests có file tạm nên chạy với quyền truy cập fixture Windows phù hợp; không ghi checkpoint nghiên cứu vào artifacts hoặc sửa snapshot/scaler.

Giới hạn: gradcheck số học dùng mạng nhỏ để giảm chi phí, không kiểm mọi điểm trong miền input hoặc chứng minh optimizer sẽ hội tụ. Mạng default được kiểm shape/backward/update/roundtrip riêng. Kết quả này nghiệm thu architecture/forward/persistence local, không chứng minh dự báo hiệu quả, early stopping/validation/official checkpoint của TV4 hoặc model/API consumer. Không đổi thuật toán ở mục3 nên giữ evidence5460 mẫu thật float64 của mục2, không chạy lặp không cần thiết. Môi trường sạch/máy khác còn mục5; trace nghiệm thu sau lưu/nạp và cập nhật là mục4 tiếp theo. Chưa push/merge/Drive hoặc thay notebook TV1.
