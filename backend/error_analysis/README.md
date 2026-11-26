# error_analysis

Phân nhóm, chọn ví dụ theo quy tắc, diễn giải kết quả Evaluation. Không viết lại metric.

validation_monitoring.py phân tích residual cùng mẫu/ngày2023, rolling20 phiên, bias/P95/max, top errors và metric tháng. MAE/RMSE gọi evaluation.one_step, không tạo implementation metric riêng. Dùng để mô tả validation sau TV5 mục9, không tuning/test hoặc nghiệm thu toàn bộ TV6. Script build_tv5_monitoring.py xuất CSV và bốn biểu đồ, có inventory telemetry đã đo/chưa đo.
