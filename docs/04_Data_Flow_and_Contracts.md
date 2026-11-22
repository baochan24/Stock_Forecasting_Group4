# Data Flow và cấu trúc trao đổi — đã thống nhất

## Nghiên cứu
Acquisition → Validation → Preparation → Models/Training → Inference → Evaluation → Error Analysis → phát hành.
Experiment Runner điều phối; management/artifacts/audit hỗ trợ xuyên suốt.

## Web
Chọn release/ngày/chế độ → API kiểm tra → lịch sử → chuẩn hóa → inference/baseline → giá gốc → ghép target nếu có → response → giao diện.

## Dataset
Bảng model: date, ticker, adjusted_close, dataset_version. Metadata: nguồn, thời điểm tải, USD, chính sách điều chỉnh, hash. Ngày YYYY-MM-DD theo phiên dataset, không cộng ngày lịch.

## Mẫu
Forecast Input: sample_id, dataset_version, forecast_origin, input_dates, input_values, lookback, forecast_length.
Target riêng: sample_id, target_dates, target_values, split, horizon_step. Inference không nhận target.
Input LSTM (B,30,1); target một bước (B,1), năm bước (B,5). CNN chuyển chiều nhưng giữ mẫu/ngày.
forecast_length là số đầu ra 1/5; horizon_step là khoảng cách 1..5.

### Biểu diễn TV2 đã triển khai (mục 8, 22/11/2026)

Giữ nguyên các trường và shape đã chốt. Record Forecast Input dùng input_dates là list 30 ngày ISO và input_values là mảng raw USD (30,1); forecast_origin là ngày cuối input. Record Target riêng dùng target_dates list H ngày, target_values mảng raw USD (H,), horizon_step list [1] hoặc [1,2,3,4,5] theo cùng thứ tự, split là train/val/test. Đây là biểu diễn vector theo mẫu, không phải 5 lần dự báo recursive.

sample_id hiện có dạng `<dataset_version>:lb30:f<H>:<forecast_origin>`; gắn cùng ID cho Input/Target, phân biệt mode và version, ổn định giữa các lần dựng từ cùng snapshot. Trong batch, X chuẩn hóa float64 (B,30,1), y chuẩn hóa float64 (B,H), thứ tự trùng các records; raw không bị thay bằng scaled. Cast tensor model chưa thuộc hợp đồng adapter đã nghiệm thu.

`backend/data/preparation/contracts.py` kiểm tra các trường, ID, version, ngày/phiên/giá/shape/scaling so với snapshot đã accept. `build_inference_inputs(inputs, scaler)` nhận list input records đồng nhất version/mode và không rỗng, trả bản sao input cùng X; không nhận target/y. Input có trường ngoài danh sách (kể cả target) bị từ chối; batch trộn mode/version hoặc trùng ID bị từ chối. Caller phải xác minh snapshot/scaler trước khi gọi adapter. Đây là chuẩn bị đầu vào, chưa phải implementation inference/API/model của TV6/TV3.
Demo lịch sử đối chiếu chỉ chọn ngày đủ input/target; ngày hợp lệ phụ thuộc release và chế độ.

## Dự báo
Mỗi hàng: release_id, dataset_version, method, run_id/model_version nếu áp dụng, baseline_version nếu persistence, forecast_origin, horizon_step, target_date, predicted_price, result_source.
Khóa: release/phương pháp/phiên bản thực nghiệm/ngày gốc/bước. Không chỉ khóa bằng target_date.
Actual và error được ghép sau theo dataset/ticker/loại giá/ngày; không truyền tương lai vào model. Persistence dùng giá gốc cuối input.

## Metric và lỗi
Metric: release/run, method, split, phạm vi forecast_origin, forecast_length, horizon_step, sample_count, MAE/RMSE, đơn vị, official_full_set hoặc selected_range.
Kiểm tra cùng tập mẫu khi so sánh; không âm thầm bỏ mẫu thiếu.
Lỗi: request/run ID, mã lỗi, bước và trạng thái. Log web tách training logs.
