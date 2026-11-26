# data/preparation

TV4 item 7 adds lookback 10/30/60 with default 30 across windowing, contracts, tensors, artifacts and audits. Existing artifacts remain loadable. common_history=True restricts targets to positions with 60 sessions of history after full coverage audit.


**Cập nhật dtype23/11/2026 theo yêu cầu người dùng:** adapter tensors.py hiện giữ X/y **CPU float64**, không còn downcast. Cả hai LSTM mặc định float64; tensor copy khớp mảng nguồn tuyệt đối, inverse rtol=atol=1e-12. Tests66/66 và5460 mẫu thật đạt; xem TV3_Progress.md phần precision. Mô tả float32 phía dưới là lịch sử mục2 trước thay đổi, không áp dụng mặc định hiện tại. Model nhận X float64, y cùng dtype dùng loss; không refit/sửa artifact TV2.

## Adapter TV3 mục 2 — 23/11/2026

`tensors.py` là adapter tùy chọn cần torch, được thêm cho consumer model; TV2 artifacts/dependencies/preprocessing không đổi. `make_lstm_inputs(inputs, scaler, dataset_version=version, forecast_length=1/5)` chỉ nhận input records sau acceptance, trả X CPU float32, inputs bản sao và IDs/version/mode, không y/targets. `make_lstm_training_batch(batch, scaler, ...)` nhận batch TV2 đã verify, kiểm tra X/y so raw records/scaler và pairing rồi cast X/y về float32 CPU, giữ metadata. Model chỉ gọi `model(packed['X'])`; y dành cho loss/evaluation ở TV4, không truyền vào model.

Dung sai cast ở standardized units rtol1e-6/atol1e-7; kiểm tra inverse target đã cast về USD rtol1e-6/atol1e-4 cho snapshot đã thử. Không nhầm với dung sai float64 TV2 1e-12. Tensor copy độc lập, không sửa arrays/artifacts; không fit/refit. Loader và audit vẫn bắt buộc trước adapter, adapter đơn lẻ không chứng minh nguồn/hash hoặc session continuity.

Tests/CLI TV3 xem reports/audits/TV3_Progress.md mục2; 63/63 tests, forward5460 mẫu thật đạt. Không có training chính thức hoặc nghiệm thu model performance.

## Mục 10 — kỹ thuật bàn giao hoàn thành local

Setup/consumer/verify tại `docs/TV2_Setup_and_Handoff.md`; kết quả/SHA gói tại `reports/audits/TV2_Final_Handoff.md`. Prepared hai modes trong data/prepared, NPZ không pickle và input/target JSON riêng, manifest gắn snapshot/scaler. `backend/artifacts/prepared.py` chỉ lưu/nạp/checksum, verify phải so nguồn trước consumer.

Venv sạch `.venv/tv2_clean` theo scripts/requirements-tv2-lock.txt, 51/51 tests; ZIP giải nén độc lập chạy tests/verify đạt và X/y/indices nạp lại bằng dựng mới. Chờ thành viên khác xác nhận, chưa nghiệm thu liên máy; chưa upload/push. Trạng thái bên dưới là lịch sử.

## Mục 9 hoàn thành local — audit leakage

`backend/audit/tv2_leakage.py` tính train moments và eligible target indices độc lập từ dữ liệu nguồn (không dùng split plan làm oracle), phát hiện thiếu/thừa/đảo mẫu và lý do loại sai, rồi đối chiếu contract/ngày/giá/scaling. CLI `.venv/tv2/Scripts/python.exe -X utf8 scripts/audit_tv2_leakage.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z` đã đạt.

Audit thật hai mode kiểm tra scaler train 2014 giá, tất cả windows, input-only adapter; cấm fit/partial_fit, state/hashes không đổi. Thử nhân 10 giá từ 2023 và 2024 trong bản sao bộ nhớ: input trước cutoff không đổi, future target đổi, train statistics và indices không đổi. Không ghi các bản sao thành artifacts.

Suite TV2 hiện 46/46 đạt. Evidence `logs/audit/tv2_leakage_20261122T144606274936Z/summary.json` có 12 ví dụ đầu/cuối mỗi split/mode với đủ input/target ngày/giá để đối chiếu. Không chứng nhận training/test-tuning hoặc point-in-time backtest; lịch sử dùng giá adjusted hồi cứu. Mục 10 đóng gói/môi trường/bàn giao còn chờ; các trạng thái dưới đây là lịch sử.

## Trạng thái mới nhất — mục 8 hoàn thành local

`contracts.py` có `validate_forecast_input(record)` và `validate_window_result(result, accepted_data, scaler)`, báo ValueError khi vi phạm hợp đồng. Kiểm tra record input/target tách biệt, ID/version/origin, ngày liên tiếp theo snapshot, raw giá/shape, target split/horizon và X/y chuẩn hóa float64. Không kiểm chứng provenance thay loader; caller phải accept snapshot/scaler trước.

`build_inference_inputs(inputs, scaler)` chỉ nhận list Forecast Input records không rỗng, đồng nhất version/mode, không trùng IDs; trả bản sao `{inputs, X}`. Không đọc target, không fit/refit, không chứa y. Input có trường thừa kể cả target bị từ chối. Dùng `batch['inputs']`, không truyền toàn bộ batch training vào inference. Đây là preparation adapter, chưa xây module inference/API của TV6.

Biểu diễn chính thức xem docs/04_Data_Flow_and_Contracts.md: raw input (30,1), raw target (H,), target_dates/horizon_step list H; scaled X (B,30,1), y (B,H), float64. ID `<version>:lb30:f<H>:<origin>` ổn định theo snapshot/chế độ. Consumer adapter float32/model chưa nghiệm thu.

CLI `.venv/tv2/Scripts/python.exe -X utf8 scripts/check_tv2_contracts.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z`: toàn bộ 2736/2724 mẫu hai mode đạt, 5460 IDs duy nhất và adapter input-only cho X bằng tuyệt đối X batch. Suite 41/41 đạt. Evidence `logs/audit/tv2_contracts_20261122T143629561606Z/summary.json`. Mục 9–10 còn chờ; các trạng thái dưới đây là lịch sử.

## Trạng thái mới nhất — mục 7 hoàn thành local 22/11/2026

`prepare_five_step_windows(project_root, dataset_version, scaler_folder)` trong windows.py xác minh TV1/scaler cũ trước khi tạo cửa sổ direct multi-output. Helper `create_five_step_windows(validated_data, scaler)` dùng chung lõi với một bước, caller phải xác minh nguồn. X=(B,30,1), y=(B,5), float64; input raw/target raw tách riêng như một bước, target có 5 ngày và horizon_step=[1,2,3,4,5]. Không recursive/fit/đưa giá tương lai vào input. ID có f5 để phân biệt f1.

Toàn bộ 5 target phải thuộc cùng split theo ngày, input vẫn lấy lịch sử từ tập trước. Mỗi batch báo excluded_insufficient_history, excluded_incomplete_targets, excluded_cross_split_targets (phân loại không trùng theo thứ tự history→incomplete→cross-split). Không bỏ dòng snapshot; chỉ loại candidate không đủ điều kiện. Batch rỗng giữ (0,30,1)/(0,5).

Audit dùng CLI cũ với cờ mới `--forecast-length 5`: `.venv/tv2/Scripts/python.exe -X utf8 scripts/check_tv2_one_step.py --forecast-length 5 --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z`. Không đổi tên script; lệnh thiếu cờ vẫn chạy một bước.

Snapshot hiện tại đạt 1980/246/498 mẫu. Train/val loại 4 candidate cắt split, test loại 4 candidate cuối chưa đủ target; train loại thêm 30 do thiếu lịch sử. Suite TV2 36/36 đạt, CLI mọi mẫu thật đạt. Evidence `logs/audit/tv2_five_step_20261122T143105318011Z/summary.json`. Chưa thực hiện mục 8–10 hoặc huấn luyện; các mục bên dưới giữ lịch sử.

## Trạng thái 22/11/2026 — mục 6 hoàn thành local

`windows.py` có `prepare_one_step_windows(project_root, dataset_version, scaler_folder)` để xác minh snapshot/scaler đã lưu rồi tạo batch; không fit. Helper `create_one_step_windows(validated_data, scaler)` chỉ dùng sau acceptance, không tự xác thực nguồn.

Kết quả chứa dataset_version, lookback=30, forecast_length=1 và splits train/val/test. Mỗi split có `inputs` (raw Forecast Input records), `targets` riêng (raw target records), `X`/`y` chuẩn hóa float64, target_indices, num_samples và excluded_insufficient_history. X=(B,30,1), y=(B,1). Raw input/target không làm tròn; mỗi sample_id kết hợp version/lb30/f1/origin. Không truyền cả batch chứa targets vào inference, chỉ truyền input record/X tương ứng. Nghiệm thu contract chung hai chế độ còn mục 8.

Mỗi target lấy đúng 30 phiên trước từ toàn chuỗi. Không tạo cửa sổ riêng cho từng tập; lịch sử của tập trước được phép dùng. Thiếu lịch sử thì ghi số target bị loại, không điền giá; batch rỗng có shape (0,30,1)/(0,1). Không đưa một target vượt cuối chuỗi, không tự tạo phiên tương lai. Entry point chỉ nhận validated snapshot đầy đủ, nên snapshot thiếu phiên bị loader từ chối.

Lệnh audit: `.venv/tv2/Scripts/python.exe -X utf8 scripts/check_tv2_one_step.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z`.

Snapshot hiện tại đạt train/val/test=1984/250/502 mẫu, không mất target đầu val/test. Suite 32/32 đạt. Evidence `logs/audit/tv2_one_step_20261122T142203997497Z/summary.json`. Mục 7/8/9/10 chưa hoàn thành; các trạng thái mục 1–5 dưới đây là lịch sử.

Trạng thái mới nhất 21/11/2026: mục 1–5 hoàn thành local. Mục 5 kiểm chứng shapes/roundtrip với scaler lưu sẵn, xem README transforms. Ghi chú mục 1–4 dưới đây giữ theo lịch sử triển khai; tiếp theo là mục 6, chưa tạo windows.

Chia tập, fit scaler train, tạo mẫu kèm ngày/split. Không fit scaler khi inference.

Trạng thái: đã tiếp nhận một phần code TV2 từ PR #2, commit `245dc5c366e3d81d2dfc2f1c2df18f3ce1e9444f`, vào `preparation.py`: `split_data` và `fit_scaler`. Đã hoàn thiện mục 1–4 local; chưa phải pipeline nghiệm thu đầy đủ.

`split_data` hiện trả dates/prices/dataset_version theo năm; phải nhận DataFrame đã được `load_tv1_snapshot` xác minh. `fit_scaler` là helper nhận mảng, không kiểm chứng ngày; pipeline `build_train_scaler` bên dưới chọn train theo kế hoạch đã kiểm tra. Không gọi windowing riêng trên từng tập trả về vì sẽ mất lịch sử trước ranh giới.

## Mục 4 — scaler train, lưu/nạp

`from backend.data.preparation.train_scaler import build_train_scaler`

`result = build_train_scaler(project_root, dataset_version)` xác minh snapshot TV1 trước, lấy toàn bộ giá train theo target_indices train (2015–2022, chưa tạo windows), gọi fit đúng một lần và lưu artifact mới. Không gọi fit với val/test. Đây là entry point dùng cho training preparation; inference chỉ dùng `backend.artifacts.scaler.load_scaler`.

`load_scaler(folder, expected_dataset_version=version, expected_source_hashes=snapshot['acceptance']['hashes'])` trả `(scaler, manifest)`. Nạp lại không fit; kiểm tra snapshot/version/hashes, class/format, phiên bản sklearn, feature/USD/train dates/count, checksum và state hữu hạn. Đây là kiểm tra nhất quán artifact cục bộ, không chống được người sửa đồng thời cả state lẫn manifest có chủ ý. Không nạp pickle.

Mỗi thư mục `artifacts/scalers/<scaler_id>/` có scaler.json và manifest.json; tạo mới độc quyền, không ghi đè. Manifest ghi hash state và 5 hash snapshot, thời điểm, phạm vi/số dòng fit. Nếu ghi lỗi giữa chừng, thư mục dở không có manifest hoàn chỉnh không được dùng; thử lại bằng ID mới, không âm thầm ghi đè/dọn run cũ.

Lệnh đã kiểm chứng:

```powershell
.\.venv\tv2\Scripts\python.exe -X utf8 scripts/build_tv2_scaler.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z
.\.venv\tv2\Scripts\python.exe -X utf8 -m unittest discover -s tests/data -p 'test_tv2*.py' -v
```

`.venv/tv2` là môi trường phát triển riêng dùng system-site-packages, cài exchange_calendars 4.13.3 tại venv; không sửa TV1. Numpy/pandas/sklearn hiện kế thừa site packages, chưa là môi trường sạch/lock hoàn chỉnh hoặc bằng chứng máy khác; việc đó còn ở mục 10. Dependencies scaler: numpy/pandas/scikit-learn, bước nhận snapshot thêm exchange_calendars. Phiên bản thực tế được ghi ở evidence/manifest.

Snapshot hiện tại: fit 2014 giá 2015-01-02→2022-12-30, mean=70.0884543582723 USD, scale=48.587429342498965 USD. Kiểm tra nạp lại transform giống hệt và roundtrip toàn bộ snapshot max abs error=5.684341886080802e-14 USD, dung sai rtol/atol=1e-12. Transform val/test chỉ kiểm tra tái lập số học, không phải đánh giá model. Mục 5 tiếp tục nghiệm thu scale/inverse theo contract shapes với scaler đã lưu.

Mục 1: đã bổ sung validation cho module nền. `split_data(path)` yêu cầu date dạng YYYY-MM-DD hợp lệ, ticker AAPL, giá hữu hạn/dương, không trùng ngày, năm 2015–2025 và cả ba tập không rỗng; sắp theo ngày và trả `dict[train/val/test]` chứa `dates: list[str]`, `prices: ndarray(N,1)`. `fit_scaler(train_prices)` chỉ nhận giá dương/hữu hạn dạng `(N,)` hoặc `(N,1)`, trả StandardScaler mới; caller phải bảo đảm mảng thuộc train. Sai dữ liệu trả ValueError; lỗi đọc file được giữ nguyên. Không tự sửa hoặc loại dòng lỗi.

Chuẩn bị/scaling dùng float64 để giữ độ chính xác; khi tạo tensor model sẽ chuyển dtype ở adapter. Đây là thay đổi dtype so với code PR float32, không đổi tên hàm hoặc shape. Xác minh nguồn/hash và giữ version là mục 2; contract mẫu và model adapter chưa triển khai.

## Mục 2 — tiếp nhận snapshot TV1

`from backend.data.preparation.snapshot import load_tv1_snapshot`

Gọi `snapshot = load_tv1_snapshot(project_root, dataset_version)` với version cụ thể; dùng `snapshot['data']` cho xử lý tiếp, giữ toàn bộ lịch sử liên tục. Kết quả còn có dataset_version, acceptance (hash/checks), quality (kiểm tra lại bằng TV1) và paths. Không tự chọn bản mới nhất hoặc tự tải/clean dữ liệu. Thiếu artifacts báo FileNotFoundError; phiên bản/hash/kiểm tra sai báo ValueError; lỗi đọc JSON/CSV được truyền ra và không nhận dữ liệu.

Cần 5 artifacts: raw CSV, metadata JSON, validated CSV, validation report và quality audit đúng version trong data/raw, data/validated, data/metadata. Tái sử dụng `inspect_standard_output` (gồm provenance/schema/hash/ánh xạ raw→validated), sau đó `inspect_raw_dataframe` kiểm tra lại lịch phiên/chất lượng; kiểm tra hash lần nữa sau khi đọc. Không ghi đè artifacts. Tính toàn vẹn cục bộ không thay thế chứng nhận độc lập từ Yahoo; lịch NASDAQ của thư viện hiện ánh xạ XNYS theo giới hạn TV1 đã công bố.

Lệnh đã chạy thành công tại workspace:

```powershell
.\.venv\tv1_clean\Scripts\python.exe -X utf8 scripts/inspect_tv2_input.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z
```

Loader/CLI cần pandas, numpy, exchange_calendars như requirements TV1; split/scaler và tests TV2 còn cần scikit-learn. Python hệ thống hiện thiếu exchange_calendars nên không chạy loader thật ở đó; môi trường tv1_clean chạy loader được nhưng chưa dùng làm môi trường đầy đủ TV2. Chưa khóa môi trường chung (mục bàn giao).

`split_data(snapshot['data'])` giữ dataset_version trong mỗi split, không sửa DataFrame đầu vào. Gọi split_data trực tiếp với CSV chỉ kiểm tra bảng, không chứng minh provenance; đường dùng cho pipeline phải qua loader. Split theo target đã có ở mục 3 dưới đây; windowing mục 6/7 chưa triển khai.

## Mục 3 — kế hoạch split theo target, giữ nguyên lịch sử

`create_split_plan(snapshot['data'])` trả `data` 4 cột được xếp theo ngày, `dataset_version`, và `target_indices` (train/val/test). Các chỉ số là vị trí dòng trong toàn bộ `data`, không phải chỉ số của từng chuỗi đã cắt. Giữ bảng đầy đủ này cho windowing; `split_data` chỉ cung cấp view phục vụ thống kê/scaler, không phải đầu vào windowing từng tập.

`target_split(target_dates)` nhận 1 hoặc 5 ngày ISO tăng dần duy nhất: trả train (2015–2022), val (2023), test (2024–2025); trả None nếu 5 target cắt ranh giới tập. Ngày lỗi/ngoài phạm vi hoặc chiều dài khác 1/5 báo ValueError. Hàm không tự chứng nhận 5 ngày là 5 phiên liên tiếp; windowing phải lấy trực tiếp từ snapshot đã kiểm tra.

Chạy audit: `.venv/tv1_clean/Scripts/python.exe -X utf8 scripts/inspect_tv2_split.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z`. Snapshot này có 2014/250/502 phiên theo split. Phiên đầu val 2023-01-03 có 30 phiên trước từ 2022-11-17 đến 2022-12-30; phiên đầu test 2024-01-02 có 30 phiên từ 2023-11-16 đến 2023-12-29. Các dòng đầu train chưa đủ lịch sử vẫn nằm trong bảng; sẽ không thành mẫu cho đến khi đủ lookback. Đây chưa phải số mẫu model.

Không fit scaler hoặc tạo windows trong mục 3. Import sklearn được trì hoãn đến lúc fit/transform để nhận snapshot và chia tập chạy được trong môi trường TV1 sạch mà không sửa môi trường này; thao tác scaler vẫn cần sklearn. Chưa công bố môi trường chung TV2 hoàn chỉnh.

Chưa tiếp nhận `create_windows` làm implementation: bản PR sai thụt lề và chưa xử lý đầy đủ context/contract. Theo dõi checklist tại `reports/audits/TV2_PR_Audit_20261120.md`. Dependencies: numpy, pandas, scikit-learn; chưa khóa môi trường TV2. Không thay môi trường TV1.
