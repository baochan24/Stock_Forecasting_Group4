# evaluation

Căn target, sai số, MAE/RMSE, số mẫu và horizon. Sở hữu phép tính metric dùng chung.

TV5 mục9 bổ sung one_step.py làm dependency tối thiểu cho phép so sánh USD trên validation. Kiểm unique sample/date keys đúng thứ tự, shape(N,1), finite và MAE/RMSE; không tự bỏ/ghép mẫu. Tests tính tay và các ca lệch mẫu ở tests/evaluation/test_one_step_comparison.py. Multi-step, đánh giá test cuối, release và tích hợp TV6 chưa nghiệm thu bởi phần này.
