# TV4 — lộ trình training/validation và thực nghiệm LSTM

## Trạng thái sau sửa audit ngày 26/11/2026

**Mục 10 đã hoàn thành local.** Bản sao độc lập kiểm payload và reload 12 model đạt, strict tests 69/69. Hai notebook đã có mục 10 và bảng tổng hợp. [Báo cáo nghiệm thu và tổng kết](TV4_Item10_Handoff.md)

Mục 1–9 đã kiểm chứng local. Đã sửa giao diện checkpoint, đồng bộ quyết định và kiểm khả năng di chuyển artifacts. Hồi quy đạt 69/69 tests, bản sao kiểm đủ 323 file và 12 model. Xem [báo cáo sửa lỗi](TV4_Audit_Fixes_20261126.md).

| Item | Status |
|---|---|
| 1 | Verified locally |
| 2 | Verified locally |
| 3 | Verified locally |
| 4 | Verified locally |
| 5 | Verified locally |
| 6 | Verified locally |
| 7 | Verified locally |
| 8 | Verified locally |
| 9 | Verified locally |
| 10 | Verified on independent local copy; recipient machine acceptance pending |

<details>
<summary>Historical progress and audit evidence</summary>


Audit mục 1–9 ngày 26/11/2026 đã chạy strict 67/67 tests và nạp lại 12 checkpoint, MSE tổng/từng horizon khớp. Phát hiện đường gọi train_model trực tiếp với checkpoint_dir còn đi vào helper lưu chưa tồn tại; runner chính thức có callback nên các checkpoint hiện có đạt. Cần sửa giao diện này và đồng bộ tài liệu trước nghiệm thu bàn giao. [Báo cáo sai sót](TV4_Items1_9_Review_20261126.md)

## Mục 9 hoàn tất

LSTM năm bước hoàn tất ba seed, tổng 300 epoch. MSE validation tổng trung bình 0,007692942, std mẫu 0,000146946. Cả ba best tại epoch 100, đã nạp lại model và kiểm MSE tổng/từng horizon. Notebook gốc và UPDATED được bổ sung mục 9, bảng và hai biểu đồ. TensorBoard đã có dữ liệu năm bước. [Báo cáo chi tiết](TV4_Item9_FiveStep_Training.md)

Audit sau mục 8 xác nhận chín run, log và hash checkpoint khớp. Bốn run chạm ngân sách 100 epoch, hai run có best ngay epoch 100, đã ghi giới hạn trong báo cáo. Cấu hình và dữ liệu thật năm bước kiểm tra lại đạt, đủ điều kiện tiếp tục mục 9 theo kế hoạch hiện tại. [Chi tiết audit](TV4_Item8_OneStep_Training.md)

Đã xuất lịch sử chín run mục 8 sang TensorBoard 2.21.0 trong môi trường dashboard riêng. Kiểm chứng đủ 775 epoch cho Loss/validation, mỗi run có 5 scalar tags. Server local 127.0.0.1:6006 phản hồi HTTP 200 và endpoint scalars có đủ 9 run. Các event là bản xuất lịch sử CSV, wall time ghi thời điểm export. Notebook gốc và UPDATED có liên kết dashboard ở mục 8.

Khôi phục notebook khi phát hiện file gốc trở về bản 17 cell, 77 KB. Đã sao lưu bản cũ, dựng lại từ builder và thực thi thành công 20/20 cell code. Bản gốc và bản UPDATED có cùng nội dung, 34 cell, 6 PNG và metadata kernel TV4. [Biên bản khôi phục](../../logs/audit/tv4_notebook_recovery_20261125T130418968047Z/summary.json)

Notebook 04 đã sửa phần giới thiệu ghi cũ mục 1–4 thành trạng thái đến mục 8, thêm bảng tổng hợp validation và liên kết đến mục 6/7/8. Đã kiểm tra lại file đúng đường dẫn workspace, 34 cells, 49 output và 6 PNG, không có error output. Gỡ trạng thái ẩn ở metadata cell và giữ đầy đủ kết quả đã thực thi.

## Mục 8 hoàn tất ngày 25/11/2026

Chín run LSTM một bước hoàn tất, tổng 775 epoch. Cả chín best checkpoint được nạp mới và đối chiếu validation MSE thành công. Lookback 30 được chọn bằng validation MSE trung bình ba seed 0,003265939, std mẫu 0,001118952. Notebook mục 8 đã bổ sung bảng và biểu đồ. [Báo cáo đầy đủ](TV4_Item8_OneStep_Training.md)

## Mục 7 đã hoàn thiện trước training

Đã mở rộng lookback 10/30/60, tạo artifacts mới và xác minh cùng 1.954 mẫu train, 250 mẫu validation cho so sánh một bước. Chốt 9 run một bước cộng 3 run năm bước tại lookback 30, seeds 42/123/456, tối đa 100 epoch và patience 10, một luồng CPU. Bốn cấu hình qua probe một epoch, lưu đủ thời gian train/validation và MSE từng horizon. Hash toàn bộ backend và YAML được ghi vào run/checkpoint. Run lỗi giữ tham chiếu checkpoint đã lưu thành công.

Hồi quy đạt 128 tests và 96 subtests. Strict TV4 đạt 67/67 trong môi trường sạch. Xem [kế hoạch cập nhật và bằng chứng](TV4_Item7_Experiment_Plan.md). Các ghi nhận chờ mục 7 ở dưới là lịch sử trước hoàn thiện. Bước tiếp theo là thực hiện các run chính thức theo kế hoạch.

Mục 7 đã audit và lập [phương án thực nghiệm](TV4_Item7_Experiment_Plan.md). Factory, windowing và prepared hiện ghim 30 phiên. Kế hoạch lookback 10/60 cần bổ sung contract/artifacts và thống nhất phạm vi trước khi khóa thiết kế. Mục 7 đang chờ quyết định này. Bảng trạng thái cũ dưới đây được giữ như lịch sử.

## Cập nhật mục 6 ngày 25/11/2026

Hai LSTM hoàn thành smoke test trên toàn bộ train/validation với seed 42, CPU float64, một luồng PyTorch và giới hạn 3 epoch. Một bước dùng 1.984/250 mẫu, 4.513 tham số, best epoch 2 và validation MSE 0,1275289. Năm bước dùng 1.980/246 mẫu, 4.645 tham số, best epoch 3 và MSE tổng 0,7876652. MSE tính trên giá chuẩn hóa. Mỗi model nạp từ checkpoint cho dự báo bằng tuyệt đối best trong RAM trên toàn bộ validation. Các số này thuộc smoke test ba epoch.

Summary ghi riêng thời gian train, validation, tổng run và median inference batch 32 qua 30 lượt sau 5 lượt làm nóng. Thời gian phụ thuộc máy và tải nền. [Bằng chứng và điều kiện CPU](../../logs/audit/tv4_item6_20261125T115308089469Z/summary.json)

Notebook lưu đủ 17/17 cell code và biểu đồ mục 6. Bộ tests chạy đạt 66/66. Tiếp theo là mục 7 chốt thiết kế thực nghiệm và ngân sách. [Biên bản notebook](../../logs/audit/member_notebooks_20261125T115047043122Z/summary.json)

Cập nhật mục 5 ngày 25/11/2026. Runner đã nối callback lưu best với contract artifacts TV3, tạo ID riêng cho mỗi epoch cải thiện. Mỗi checkpoint gồm weights.pt, manifest, dataset/scaler và năm hash nguồn, seed, cấu hình và best epoch/loss. Phép thử một bước dùng 33 cửa sổ đầu mỗi tập, khởi tạo model mới từ checkpoint rồi đối chiếu dự báo toàn bộ validation với best trong RAM bằng dung sai 0. Epoch tốt nhất là 1, dừng ở epoch 11, MSE best 2,5213520671710237. Bằng chứng này nghiệm thu lưu/nạp trên tập con của LSTM một bước. Smoke hai horizon và đo CPU tiếp tục ở mục 6.

Bộ tests đạt 66/66. Notebook đã lưu output 16/16 cell code, gồm mục 5. [Biên bản checkpoint](../../logs/audit/tv4_item5_20261125T114321598598Z/summary.json) · [Biên bản notebook](../../logs/audit/member_notebooks_20261125T114053853666Z/summary.json)

Ngày 25/11/2026, TV4 đã hoàn thành mục 1–4 tại workspace. Bộ kiểm thử đạt 66/66 và notebook 04 đã lưu output 15/15 cell code. Mục 4 xác minh khôi phục trọng số tốt nhất trong RAM. Mục 5 sẽ kiểm tra lưu checkpoint và nạp vào một model mới.

Cơ sở: rule.md, đề Topic4, docs/01/03/04/10/11/12, docs/TV3_Handoff_TV4_TV6.md và reports/audits/TV4_TV5_PR9_PR10_Audit_20261125.md. Nguồn dự kiến: nhánh TV4, PR#10, commit16555929210314b1eb06da9dc84b827ececc1b9e; kiểm lại remote trước tiếp nhận nếu có cập nhật.

## Đích và phạm vi

TV4 nhận hai model LSTM CPU float64 của TV3 và prepared/scaler/version đã accept của TV2; cung cấp training loop dùng chung, config/seeds, loss logs/thời gian CPU, checkpoint chọn bằng validation có thể reload và bằng chứng tái lập. LSTM một/năm bước train riêng, không dùng test để chọn cấu hình hoặc seed. Không triển khai CNN, API/frontend hoặc viết lại preprocessing/evaluation TV6.

## Flow cố định gồm10 hạng mục

| Mục | Công việc | Đầu ra/điều kiện nghiệm thu | Trạng thái |
|---|---|---|---|
| 1 | Tiếp nhận source, sửa layout/import và dựng môi trường TV4 | Chọn code PR#10 cần dùng vào đúng backend/training, backend/experiments/runner và management; config/tests tương ứng. Venv riêng và dependencies có PyYAML, không sửa venv TV1–TV3. Tests hiện có chạy trực tiếp từ workspace, không alias/import từ checkout audit | Đạt local25/11/2026 —16/16 tests |
| 2 | Đồng bộ contract và dtype CPU float64 | Bỏ cast float32 cứng; kết nối LSTMOneStep/LSTMMultiStep hiện hành, X(B,30,1), y(B,1)/(B,5), kiểm dtype/device/shape/model-horizon. Không đổi precision/model TV3 hoặc global torch dtype | Đạt local25/11/2026 —52/52 tests |
| 3 | Nối dữ liệu TV2, factory và config AAPL thật | Xác minh snapshot, scaler và prepared. Kiểm tra model factory, train/validation loaders, ID, ngày và batch cuối trên dữ liệu AAPL | Đạt local 25/11/2026 |
| 4 | Nghiệm thu training/validation và quản lý run | Adam/MSE, MSE có trọng số theo số mẫu, train/eval, kiểm tra loss/gradient/trọng số hữu hạn, patience và khôi phục best trong RAM. Ghi cấu hình, nguồn, seed, CPU/thread, lịch sử epoch và trạng thái lỗi | Đạt local 25/11/2026 |
| 5 | Nối checkpoint thật và reload | Dùng/đồng bộ contract artifacts LSTM của TV3, ID mới cho snapshot bất biến; không gọi hàm save_checkpoint chưa tồn tại. Có dataset_version,5 source hashes,scaler_id,run_id,seed/config,best_epoch/val_loss và selected_on=validation. Nạp instance mới từ file thật, output/validation khớp best epoch; không chỉ load bản sao RAM | Verified locally; see corresponding item report |
| 6 | Smoke training AAPL và đo CPU | Run ngắn giới hạn trên train/validation cho cả hai horizon; loss/gradient/weights hữu hạn, biểu đồ/logs, reload đạt. Gắn nhãn diagnostic, ghi tổng runtime và đo riêng train/inference có điều kiện CPU rõ ràng; chưa chọn model bằng test | Verified locally; see corresponding item report |
| 7 | Chốt thiết kế thực nghiệm và ngân sách | Ghi cấu hình/seeds trước runs cuối; validation chọn cấu hình, không test. Dựa đoCPU để xác định kế hoạch lookback10/30/60 và ngân sách hữu hạn; so lookback dùng giao target dates hợp lệ và scaler train theo contract. Không tự bỏ thí nghiệm hoặc nhận cấu hình khởi đầu là tối ưu | Verified locally; see corresponding item report |
| 8 | Huấn luyện chính thức LSTM một bước | Chạy3 seeds đã chốt, best checkpoint từng seed, train/val curves, config/hash/provenance/thời gian CPU/số tham số, reload thật; khóa cấu hình trước test và không chọn seed thắng test | Verified locally; see corresponding item report |
| 9 | Huấn luyện chính thức LSTM năm bước | Model khởi tạo và checkpoint riêng; cùng loop,3 seeds, MSE tổng trọng số horizon bằng nhau để chọn best, theo dõi validation từng bước1–5. Không đưa target tương lai vào model, bảo đảm cả5 target cùng split | Verified locally; see corresponding item report |
| 10 | Audit cuối, tái lập và bàn giao TV5/TV6 | Venv/lock, tests/source/configs/lệnh chạy và reload; bản sao độc lập, notebook đủ outputs, checkpoint và manifests/logs có checksum. TV5 nhận loop/factory contract; TV6 nhận checkpoints/scaler/config/seeds để đánh giá. Máy khác/consumer acceptance ghi riêng nếu chưa xác nhận | Chờ9 |

Trong mục1 ưu tiên giữ code dùng được và sửa layout; những unit tests dùng mock checkpoint có thể giữ để kiểm logic, nhưng không được lấy chúng thay bằng chứng persistence mục5. Không nhận cả nội dung nhánh TV4 bằng cách ghi đè source TV3 hoặc báo cáo chung.

Mục4 kiểm logic chọn best, mục5 mới kiểm lưu/nạp từ đĩa thật. Helper TV3 chỉ lưu model weights và metadata, chưa có resume optimizer state; không thêm resume như yêu cầu bắt buộc mới nếu chưa có nhu cầu. Nếu save theo từng cải thiện validation, dùng checkpoint_id mới và ghi tham chiếu best, không ghi đè snapshot cũ.

## Các lựa chọn cần xác nhận bằng thiết kế và bằng chứng

- Dtype CPU float64 đã được người dùng chọn cho đường LSTM; không mở lại float32 để né lỗi training loop.
- Adam/MSE, batch32, learning rate0.001, tối đa100 epoch, patience10 là cấu hình khởi đầu project. Chưa tự gọi là cấu hình tối ưu.
- PR#10 đề xuất seeds42/123/456. Kiểm/chốt bộ seeds và ngân sách trước runs cuối trong mục7, ghi Decision Log; không chọn seeds từ kết quả test.
- Gradient clipping chưa được chốt; không bật ngầm. Nếu cần, xác định ngưỡng và ghi cấu hình/lý do trước runs liên quan.
- Mục7 quy định rõ thí nghiệm lookback nào chạy, số lần thử và tiêu chí validation; quyết định giới hạn dựa CPU phải được ghi nhận, không tự tuyên bố đã hoàn thành lookback10/60 chỉ vì chạylookback30.
- Test2024–2025 không đi vào train_loader/val_loader và không dùng theo dõi chất lượng để tuning. Schema/hash/coverage có thể kiểm; metric test chính thức do TV6 sau khi khóa cấu hình.

## Theo dõi bằng notebook và báo cáo

Khi bắt đầu mục1, tạo `notebooks/04_TV4_Training_and_Experiments.ipynb`, đồng bộ builder/executor trong scripts. Mỗi mục có cells giải thích mục tiêu/input/output, gọi backend/scripts và kiểm chứng/assertions/bảng/biểu đồ, lưu outputs thật. Notebook không chứa một training pipeline thứ hai. Kế hoạch này chưa tạo notebook rỗng hoặc outputs giả.

Sau mỗi mục: cập nhật trạng thái/evidence/lệnh/môi trường/giới hạn trong báo cáo này, README liên quan và notebook04; cập nhật FILE_STRUCTURE khi thêm file. Chạy cells bị ảnh hưởng, giữ phần TV1–TV3 và nội dung báo cáo thành viên khác. Source/docs/config/report vào Git có chủ đích; dữ liệu/scaler/checkpoint/logs/ZIP/venv bàn giao riêng theo quy tắc.

## Tiêu chí kết thúc TV4 trước khi chuyển TV5

- Code và integration tests chạy đúng workspace, không dựa mock cho checkpoint hoặc alias cho imports.
- LSTM một/năm bước có runs chính thức, checkpoints validation-selected và provenance/reload/logs tương ứng, theo seeds/ngân sách đã chốt.
- Notebook04 hiển thị quy trình và kết quả thật; tài liệu setup/consumer có thể thực hiện lại. Ghi rõ kỹ thuật local và phần liên máy còn chờ.
- Training loop chung sẵn sàng cho TV5; không đòi hỏi đã có CNN hoặc bảng so sánh CNN để nghiệm thu phạm vi TV4. Đánh giá test/so sánh cuối của TV6 tiếp tục là công việc sau, không bị coi là TV4 đã làm.

## Mục1 — kết quả thực hiện25/11/2026

- PR#10 head vẫn16555929210314b1eb06da9dc84b827ececc1b9e khi kiểm tra GitHub. Tiếp nhận9 file nguyên byte từ checkout audit sạch; runner đặt dưới backend/experiments/runner, không tạo bản trùng trong management. Không tiếp nhận lại LSTM, source TV1/TV2 hoặc ghi đè báo cáo chung từ nhánh thành viên.
- Provenance `logs/audit/tv4_item1_20261125/intake.json`: mapping9 file, SHA256, commit,125 protected file hashes. Hash source tiếp nhận khớp;125 file TV1–TV3/data/scaler được kiểm trước/sau, không thay đổi. Notebook01/02/03 và lock TV3 giữ nguyên.
- Tạo `.venv/tv4_clean`, CPython3.13.7, torch2.14.1+cpu, pytest9.2.0, PyYAML6.0.3; lock69 dependencies, không kế thừa system/user packages, imports từ đúng prefix. Lần tạo venv đầu trong sandbox lỗi ensurepip; đã tạo/cài lại thành công với quyền filesystem phù hợp, không tính lần lỗi môi trường là test đạt.
- `scripts/run_tv4_checks.py --require-clean`: **16/16 tests đạt,0 fail/error/skip**, source unchanged, workspace_imports=true, pip-check exit0, lock khớp, torch không CUDA. Receipt `logs/audit/tv4_tests_20261125T024653609740Z/summary.json`; cùng thư mục có pytest.log, junit.xml, pip-check.log, requirements-freeze.txt.
- Notebook `notebooks/04_TV4_Training_and_Experiments.ipynb`: **9 cells,5/5 code cells chạy đạt**, không error outputs, dùng tv4_clean và kernel riêng aapl-coursework-tv4. Receipt `logs/audit/member_notebooks_20261125T024738628366Z/summary.json`. Notebook gọi runner mới, hiển thị đủ16 testcase/JUnit, imports, source intake, lock/environment và trạng thái10 mục. Kết quả tests thực chạy lần notebook có evidence path trong output.
- Builder/executor hỗ trợ --member4; khi chỉ chọn4 không thay notebook/kernel2–3. Đã đăng ký user kernel AAPL Coursework TV4 (CPU), argv trỏ tv4_clean. Hướng dẫn docs/TV4_Setup_and_Reproduce.md.
- Scope: tests tổng hợp, checkpoint mock và epoch-loss mocks; test hồi quy tuyến tính không phải huấn luyện AAPL. Giữ nguyên castfloat32 của bản tiếp nhận để xử lý riêng mục2; version mẫu chờ3, persistence thật chờ5. Chưa nghiệm thu pipeline training hoàn chỉnh, máy khác hoặc forecasting accuracy.
- Không merge/push/Drive, không thực hiện CNN hoặc train AAPL. TV5 giữ kế hoạch chờ sau TV4.

## Mục2 — contract CPU float64 (25/11/2026)

- `trainer.py` thay đổi có chủ đích sau intake: `_read_batch(...,model=...)` giữ nguyên dtype, không dùng castfloat32; kiểm dtype input/target khớp model, CPU và giá trị hữu hạn. Hai model LSTM TV3 bắt buộc float64, một feature, target đúng horizon1/5. Shape mặc định(B,30,1), hỗ trợ10/60 ở ranh giới theo kế hoạch; chưa chạy thí nghiệm lookback.
- `_model_contract` từ chối LSTM đã downcast/mixed dtype/nonCPU; bỏ tự động model.to(cpu), không tự sửa model để né lỗi. Generic models dùng dtype của chính parameters để giữ loop chung; chưa quyết định dtype CNN. Output phải khớp target dtype/device và shape trước MSE, không implicit promotion/broadcasting.
- Giữ nguyên thuật toán/model/weights nguồn TV3 và global torch default dtype. Source trainer khác bản intake là thay đổi của mục2; receipt intake và các logs mục1 vẫn giữ nguyên như bằng chứng lịch sử.
- Bổ sung `tests/training/test_tv4_float64_contract.py`:36 cases mới, tổng **52/52 đạt**,0 fail/error/skip. Gồm cả hai LSTM default hidden32, Adam/backward thực, optimizer moment buffers64, validation không đổi weights/gradient, batch cuốiB1, NumPy values giữ tuyệt đối, từ chối sai dtype/device/shape/horizon/NaN và model downcast. Device guards dùng meta tensors để kiểm từ chối, không tuyên bố đã chạy GPU.
- Baseline suite receipt `logs/audit/tv4_tests_20261125T025249138767Z/summary.json`; tests chạy lại trong notebook với receipt mới `logs/audit/tv4_tests_20261125T025453235869Z/summary.json`. Venv/pins/imports/pip-check vẫn đạt, protected changes=[] và source không đổi trong lúc tests.
- `scripts/check_tv4_float64.py` dùng3 mẫu tổng hợp mỗi horizon, train/validation batches[2,1], xác nhận Adam update, validation giữ nguyên weights/gradient, input không đổi, float32 bị từ chối. Receipt `logs/audit/tv4_float64_20261125T025518682992Z/summary.json`. Loss là MSE tổng hợp, không MAE/RMSE giá AAPL; không lưu checkpoint.
- Notebook04: **11 cells/6 code,6/6 đạt**, có bảng52 tests và bảng probefloat64. Receipt `logs/audit/member_notebooks_20261125T025445100839Z/summary.json`.125 protected files TV1–TV3/data/scaler hash vẫn khớp; notebook01/02/03 và lock69 của TV4 không đổi.
- Tổng hợp `logs/audit/tv4_item2_20261125/summary.json`. Chưa nối factories/dataset thật (mục3), chưa nghiệm thu training/run manager đầy đủ (mục4), checkpoint hook vẫn mock trong tests/chờ mục5. Không train AAPL, push/merge/Drive hoặc triển khai TV5.

## Mục 3 — AAPL từ bộ bàn giao TV2 tới hai LSTM

Hai YAML ghim dataset_version `aapl_2015_2025_acq_20261119T141302002415Z`, ID scaler/prepared và SHA256 của hai manifest. Factory dùng lại quy trình TV1/TV2 để kiểm tra năm hash nguồn, thống kê scaler từ giá train, payload và độ phủ theo lịch phiên. TV2 kiểm tra hợp đồng trên cả ba phân đoạn. TV4 chỉ tạo loader cho train và validation. Batch giữ ID bên cạnh X/y, dataset lưu origin và toàn bộ ngày target tương ứng.

Mình chọn thứ tự thời gian cho cả hai loader ở bước tích hợp. CLI chạy model ở chế độ inference qua từng batch, đối chiếu ID và tensor theo thứ tự, kiểm tra đầu ra hữu hạn đúng shape CPU float64. Bảng ghi khoảng ngày target, tính đến target cuối cùng của cửa sổ.

| Horizon | Tập | Mẫu | Batch | Mẫu trong batch cuối | Khoảng ngày target |
|---|---|---:|---:|---:|---|
| 1 | Train | 1.984 | 62 | 32 | 2015-02-17 đến 2022-12-30 |
| 1 | Validation | 250 | 8 | 26 | 2023-01-03 đến 2023-12-29 |
| 5 | Train | 1.980 | 62 | 28 | 2015-02-17 đến 2022-12-30 |
| 5 | Validation | 246 | 8 | 22 | 2023-01-03 đến 2023-12-29 |

Cả hai validation bắt đầu dự báo từ phiên 2022-12-30 cho target đầu 2023-01-03. Với horizon 5, cả năm target của một mẫu phải nằm trong một tập. Đối chiếu sau thực thi xác nhận đủ 125 file được bảo vệ khớp SHA256 của receipt mục 1.

- Dữ liệu thật, hash manifest, năm hash nguồn, ID đầu/cuối và hash thứ tự mẫu nằm ở `logs/audit/tv4_item3_20261125T031915593224Z/summary.json`.
- Bộ tests gồm 52 ca cũ và 7 ca mới, đạt 59/59. JUnit và pytest log ở `logs/audit/tv4_tests_20261125T031805181117Z/`.
- Notebook 04 đã lưu output của 7/7 cell code. Receipt ở `logs/audit/member_notebooks_20261125T031738461569Z/summary.json`.

Phần minh họa dưới đây là bằng chứng bổ sung cho mục 3.

### Minh họa quá trình học trong mục 3.1 của notebook 04

LSTM dự báo một phiên dùng 1.984 mẫu train, 250 mẫu validation, seed 42 và Adam với learning rate 0,001. Sau lần cập nhật trên batch đầu gồm 32 mẫu, dự báo cho cửa sổ đầu thay đổi từ −0,148748 thành −0,161221 so với target −0,858999 trên thang chuẩn hóa.

Lần chạy 5 epoch khởi tạo lại mô hình từ cùng seed. Validation MSE thấp nhất trong lần minh họa là 0,127529 ở epoch 2, tăng lên 0,607479 ở epoch 3 rồi giảm còn 0,179933 ở epoch 5. Bảng và biểu đồ được lưu ngay dưới cell. Lần minh họa chỉ dùng train và validation.

- Lịch sử từng epoch nằm tại [history.csv](../../logs/audit/tv4_training_demo_20261125T032810000590Z/history.csv).
- Notebook chạy thành công 11/11 cell code. [Biên bản thực thi](../../logs/audit/member_notebooks_20261125T032435904795Z/summary.json)

#### Bổ sung biểu đồ theo dõi quá trình học

Chạy lại notebook bằng `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/execute_member_notebooks.py --member 4`. Cả 13 cell code đã thực thi và 3 hình PNG được nhúng vào notebook. Hình đầu theo dõi cửa sổ 30 phiên và thay đổi trọng số đầu ra sau batch đầu. [Biên bản chạy](../../logs/audit/member_notebooks_20261125T033114940552Z/summary.json) · [Hình cửa sổ và trọng số](../../logs/audit/tv4_training_demo_20261125T033338576395Z/01_window_and_weights.png)

Hình thứ hai tổng hợp 310 lần cập nhật trong 5 epoch. MSE từng batch được đối chiếu theo số mẫu với train MSE của trainer. Cả hai chuỗi train và validation MSE đều khớp lần minh họa trước. [Loss từng epoch và batch](../../logs/audit/tv4_training_demo_20261125T033338576395Z/02_epoch_and_batch_loss.png) · [Bảng batch](../../logs/audit/tv4_training_demo_20261125T033338576395Z/train_batches.csv)

Hình cuối thể hiện giá điều chỉnh và sai số có dấu của từng phiên validation sau khi đổi về USD bằng scaler TV2. Epoch 2 có validation MSE thấp nhất trong 5 epoch, nhưng dự báo thấp hơn giá thực ở 171/250 phiên. Số phiên này mô tả hướng sai số cho lần chạy seed 42. [Giá và sai số theo phiên](../../logs/audit/tv4_training_demo_20261125T033338576395Z/03_validation_prices_and_errors.png) · [Bảng giá validation](../../logs/audit/tv4_training_demo_20261125T033338576395Z/validation_usd.csv)

#### Kiểm tra chạy riêng mục 3.1 từ VS Code

Đã tái hiện `ModuleNotFoundError` khi Python khởi động ở `notebooks/` rồi import `backend` trước bước thiết lập đường dẫn. Cell đầu mục 3.1 nay tự tìm gốc project và nạp các import cần cho phần minh họa. Đã chạy riêng 6/6 cell code từ kernel TV4 mới ở `notebooks/`, tạo đủ 3 hình. Chạy toàn bộ notebook qua script cũng đạt 13/13 cell code. [Lịch sử chạy riêng](../../logs/audit/tv4_training_demo_20261125T033711910112Z/history.csv) · [Biên bản chạy toàn bộ](../../logs/audit/member_notebooks_20261125T033632695023Z/summary.json)

## Mục 4 — nghiệm thu vòng huấn luyện và quản lý run

Chạy `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/execute_member_notebooks.py --member 4`. Notebook gọi bộ kiểm thử sạch và `scripts/check_tv4_training_run.py`. Cả 66 ca kiểm thử đạt. Các ca mới kiểm MSE khi batch cuối ngắn, gradient và trọng số không hữu hạn, validation hòa hoặc xấu đi sau cải thiện, khôi phục best, bảo toàn hai epoch đã ghi khi epoch 3 bị lỗi hoặc bị ngắt. Runner ghi seed, cấu hình, hash nguồn, CPU, số luồng, trạng thái và lỗi của run. [Log pytest](../../logs/audit/tv4_tests_20261125T034920301420Z/pytest.log)

Phép thử AAPL dùng 33 cửa sổ đầu mỗi tập, batch 32 + 1, seed 42 và một luồng tính toán PyTorch. Target train từ 17/02 đến 02/04/2015, validation từ 03/01 đến 17/02/2023. Trainer chạy tối đa 100 epoch, dừng ở epoch 11 sau 10 epoch liên tiếp không cải thiện so với epoch 1. Validation MSE ở epoch cuối là 2,755586. Sau khi phục hồi trọng số epoch 1 trong RAM, đo lại MSE trên cùng 33 mẫu được 2,5213520671710237, khớp giá trị best đã ghi. Đơn vị là bình phương giá chuẩn hóa. Phép thử này nghiệm thu hành vi của trainer trên tập con đã nêu. [Biên bản và đường dẫn run](../../logs/audit/tv4_item4_20261125T035148068356Z/summary.json) · [CSV 11 epoch](../../logs/audit/tv4_item4_20261125T035148068356Z/runs/lstm_one_step__item4_first33_ram__seed42__20261125_105206_861414/epoch_logs.csv)

Notebook 04 đã lưu bảng, đường loss, mốc best và mốc dừng tại mục 4. Việc lưu và nạp lại checkpoint từ đĩa thuộc mục 5. [Biên bản notebook](../../logs/audit/member_notebooks_20261125T034839806427Z/summary.json)

</details>
