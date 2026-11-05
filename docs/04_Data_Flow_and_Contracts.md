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
Demo lịch sử đối chiếu chỉ chọn ngày đủ input/target; ngày hợp lệ phụ thuộc release và chế độ.

## Dự báo
Mỗi hàng: release_id, dataset_version, method, run_id/model_version nếu áp dụng, baseline_version nếu persistence, forecast_origin, horizon_step, target_date, predicted_price, result_source.
Khóa: release/phương pháp/phiên bản thực nghiệm/ngày gốc/bước. Không chỉ khóa bằng target_date.
Actual và error được ghép sau theo dataset/ticker/loại giá/ngày; không truyền tương lai vào model. Persistence dùng giá gốc cuối input.

## Metric và lỗi
Metric: release/run, method, split, phạm vi forecast_origin, forecast_length, horizon_step, sample_count, MAE/RMSE, đơn vị, official_full_set hoặc selected_range.
Kiểm tra cùng tập mẫu khi so sánh; không âm thầm bỏ mẫu thiếu.
Lỗi: request/run ID, mã lỗi, bước và trạng thái. Log web tách training logs.
