# System Architecture — đã thống nhất

Năm thành phần logic, không phải năm dịch vụ:
1. Quy trình nghiên cứu: thu thập, train/validation, test, phân tích lỗi.
2. Logic Deep Learning dùng chung: dữ liệu, transforms, models, baselines, inference, metric.
3. Bộ dữ liệu/model/kết quả có phiên bản: liên kết checkpoint, scaler, cấu hình, dataset, logs và audit.
4. Back-end API: kiểm tra yêu cầu, điều phối service và cung cấp kết quả/truy vết.
5. Front-end: tương tác, trình bày; không train, fit scaler hoặc tự tính metric khác back-end.

Training chạy riêng. API đọc release đã chọn; không tự chọn checkpoint mới nhất. Front-end gửi release_id cụ thể để tránh trộn phiên bản. Giá target chỉ dùng học/đối chiếu, không đưa vào inference.

Framework API/front-end, cơ sở lưu trữ và cách triển khai chưa chốt.
