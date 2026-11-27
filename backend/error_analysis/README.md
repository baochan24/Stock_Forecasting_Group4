# error_analysis

`train_drift_reference.py`: tham chiếu chẩn đoán origin+meanchange fit trênwindowtrain trước cutoff, từ chối targetvalidation/tươnglai. Không làmodelrelease hoặc thaypersistence. CLIcheck_tv6_lstm_learning.py phối hợpgradientdiagnostics; audit riêng, khôngoptimizerstep. Xemreports/audits/TV6_LSTM_Learning_Check.md.

Phân nhóm, chọn ví dụ theo quy tắc, diễn giải kết quả Evaluation. Không viết lại metric.

`lstm_diagnostics.py`: TV6 mục6, summary/month/year/rolling20/top10/stress theo từngcohort/seed/horizon; gọi metric Evaluation. `history_controls` giữ origin, tạo input phẳng/đảo/xáo trộn prefix cho sensitivity trên development. Không train, không chọn model hoặc suy causal. CLI scripts/analyze_tv6_item6.py vàaudit_tv6_item6.py; báo cáo reports/audits/TV6_Item6_Error_Analysis.md.

validation_monitoring.py phân tích residual cùng mẫu/ngày2023, rolling20 phiên, bias/P95/max, top errors và metric tháng. MAE/RMSE gọi evaluation.one_step, không tạo implementation metric riêng. Dùng để mô tả validation sau TV5 mục9, không tuning/test hoặc nghiệm thu toàn bộ TV6. Script build_tv5_monitoring.py xuất CSV và bốn biểu đồ, có inventory telemetry đã đo/chưa đo.
