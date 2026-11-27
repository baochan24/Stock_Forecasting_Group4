# TV6 — protocol đánh giá cuối v1

Khóa tại mục2 trước model inference/metric test. File máy đọc experiments/configs/tv6_evaluation_protocol_v1.json, semantic SHA256. Lệnh scripts/lock_tv6_protocol.py tạo mới nếu chưa có; lock đã tồn tại chỉ được kiểm, không ghi đè thay đổi. Source guard backend/audit/tv6_protocol.py đối chiếu120 artifacts/source hashes và protocol fixed policy.

Sau audit, lock có registry riêng tại experiments/configs/tv6_evaluation_protocol_v1.registry.json để ghim SHA256 bytes và fingerprint, cùng receipt cũ. V1 được đăng ký tường minh bằng --register-existing sau khi kiểm receipt trước đó, không đổi file v1. Lệnh bình thường không tự nhận một lock cũ chưa registry. Nếu mất lock hoặc mất cả lock/registry nhưng còn receipt lịch sử, từ chối tự tạo lại. Lần tạo đầu tiên thực sự chưa có lịch sử mới được bootstrap. Không dùng --register-existing để ghi đè registry hoặc hợp thức hóa drift.

Mọi path phải tương đối và nằm trong root, references model/weights/manifest/prepared/scaler phải nằm trong bảng hash intake. Model/run/seed/epoch/provenance đối chiếu manifest thực. Cohort phải khớp tất cả eligible dates/history từ snapshot, không chỉ có đúng số mẫu. Guards explicit vẫn chạy dưới Python -O, format_version không chấp nhận bool/float thay int.

## Models và tập mẫu

Giữ9 checkpoints accepted,3 seeds42/123/456 cho LSTM một bước lookback30, CNN một bước lookback30 và LSTM direct năm bước lookback30. Best epoch/config/seed đã nghiệm thu bằng validation/history ở mục1. Giữ scaler fit2015–2022, dữ liệu version đã khóa, không refit/retrain. CPU float64,1 Torch thread, batch32, không shuffle/drop_last.

Test full target split2024–2025. Một bước502 ordered samples cho LSTM/CNN/persistence; năm bước498 ordered windows cho LSTM/persistence. Cohort fingerprint dùng sample_id/forecast_origin/target_dates, source payload hash khóa cả giá. Tất cả5 targets cùng split, được đi qua ranh giới2024→2025 vì đều trong test; không yêu cầu cùng năm lịch. Các mode cópopulation khác nhau, không trộn hoặc so trực tiếp metric h1 overall với h5 overall như cùng một nhiệm vụ.

Đánh giá rolling history đã quan sát, checkpoint/scaler cố định. Khi origin dịch sang ngày tiếp theo, được dùng giá quá khứ đã quan sát ở test, không dùng target tương lai của lần dự báo đó; không update weights. H5 direct multi-output, không recursive. Đây không phải500 dự báo độc lập từ một origin cố định hoặc mô phỏng đầu tư point-in-time.

## Metrics và tổng hợp

Hai metric chính MAE/RMSE USD, giá adjusted close, không làm tròn trước tính toán. Báo đầy đủ từng model/seed/horizon/sample_count/split/range/protocol_id. H5 báo riêng từng horizon1–5. Overall h5 là flatten toàn bộN×5 residuals, MAE=mean absolute error, RMSE=sqrt(mean squared error); không trung bình5 RMSE để giả làm overall.

Từng seed tính metric riêng, sau đó mean và sample std ddof1 của3 seed. Không pooling predictions thành ensemble hoặc chọn seed có test tốt nhất. Persistence deterministic báo một bộ metric, không giả lập3 runs hoặc std từ seeds. Khi so sánh phải cùng ordered keys/actual và cùng horizon. Thiếu/trùng/lệch mẫu làm fail phép so sánh, không tự lấy intersection để làm đẹp số.

Tie atol1e-12USD chỉ xử lý ngang nhau trong dung sai tính toán float64, không phải ngưỡng cải thiện thực tiễn. Báo chênh lệch số; MAE/RMSE trái chiều là tradeoff, không thêm composite score. Chưa có practical-significance threshold hoặc statistical significance test được chốt; không dùng3 seeds hoặc các cửa sổ chồng lấn h5 làm mẫu độc lập để khẳng định significance.

## Demo và phân tích lỗi

Agent chọn mặc định seed42 cho từng neural group trong scope hoàn thành mục2, minh bạch trước test. Demo hiển thị các methods hỗ trợ, không tự chọn phương pháp thắng test. Ba run IDs demo đã pin trong protocol; không tải checkpoint mới nhất. Research report vẫn giữ đủ3 seeds. Đây không phải tuyên bố seed42 tốt nhất.

Rolling MAE20 phiên và top10 absolute errors mỗi run là cấu hình phân tích mô tả; báo signed residual/p95/bias nếu có ở mục6. Full-test metrics là chính thức, subsets theo tháng/năm/ngày phải gắn nhãn exploratory/selected_range, không thay full-test hoặc dùng để tuning. Chỉ giữ số mẫu đủ rolling window; các vị trí chưa đủ history của chart để trống, không loại khỏi full metric.

## Giới hạn và quản lý thay đổi

Không train/refit/tuning/model/seed/checkpoint selection theo test. Drift artifacts/cohort/policy khiến protocol cũ không còn hợp lệ, cần phiên bản mới có lý do và ghi mọi test exposure; không âm thầm ghi đè. Nếu một run kỹ thuật lỗi, log lỗi và xử lý tương thích trong cùng contract, không bỏ seed hoặc chọn cấu hình theo metric đã thấy.

Adjusted close có điều chỉnh hồi cứu, không đại diện point-in-time information; ngân sách tìm lookback LSTM và CNN cố định khác nhau. Các limits này giữ trong kết luận. Final test/API/release/production không được coi hoàn thành từ protocol. Mục2 không tính model predictions/metric test, frontend tiếp tục chờ đúng flow.

Registry/checksums kiểm consistency local, không phải chữ ký xác thực hoặc bằng chứng tuyệt đối không có test exposure ngoài các scripts này. Inference/evaluation các mục3–5 phải gọi validator mặc định có registry và ghi run/protocol hash trước đánh giá. Tự đặt flag false không chứng minh chưa xem test.
