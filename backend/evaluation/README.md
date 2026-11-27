# evaluation

TV6 mục4 thêm forecast_records.py, evaluate_forecast_records(predictions,actuals,protocol=...,split='val',forecast_lengths=(1,5)). Caller phải xác minh protocol/artifacts và actual source trước. Kiểm full coverage/methods/3seeds, context/keys theo đúng thứ tự, không silent inner join/drop; per-horizon/overall USD qua one_step metric chung, seed mean/std ddof1, baseline deterministic riêng. Overall không có horizon_step, error_count=N×H khác sample_count=N. Full-test cohort phải khớp protocol nhưng mục4 chỉ nghiệm thu validation và fixtures tổng hợp, chưa final test.

Căn target, sai số, MAE/RMSE, số mẫu và horizon. Sở hữu phép tính metric dùng chung.

TV5 mục9 bổ sung one_step.py làm dependency tối thiểu cho phép so sánh USD trên validation. Kiểm unique sample/date keys đúng thứ tự, shape(N,1), finite và MAE/RMSE; không tự bỏ/ghép mẫu. Tests tính tay và các ca lệch mẫu ở tests/evaluation/test_one_step_comparison.py. Multi-step, đánh giá test cuối, release và tích hợp TV6 chưa nghiệm thu bởi phần này.
