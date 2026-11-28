## Tổng kết hiện hành — audit mục10, 28/11/2026

| Giai đoạn | Phương pháp | H | MAE USD | RMSE USD | Mẫu |
|---|---|---:|---:|---:|---:|
| original_locked_test | cnn | 1 | 8.162562 | 10.073087 | 502 |
| original_locked_test | lstm | 1 | 10.896342 | 14.031708 | 502 |
| original_locked_test | lstm | 5 | 12.603942 | 16.155448 | 498 |
| original_locked_test | persistence | 1 | 2.476989 | 3.654583 | 502 |
| original_locked_test | persistence | 5 | 4.632497 | 6.707243 | 498 |
| post_development_old_test | lstm_residual | 1 | 2.465892 | 3.652078 | 502 |
| post_development_old_test | lstm_residual | 5 | 4.607636 | 6.682840 | 498 |
| post_development_old_test | persistence | 1 | 2.476989 | 3.654583 | 502 |
| post_development_old_test | persistence | 5 | 4.632497 | 6.707243 | 498 |

Số model là mean3seeds42/123/456; baseline một quy tắc,không nhân thành3runs. Std mẫu ddof1 vàtừnghorizon nằm trong evidence CSV; bảngtrên chỉH1/H5overall. MeanRMSEcủa3seedkhôngphảiRMSEensemble. Originaltest vàpost-developmentoldtest khôngtrộnthànhmộtphépkiểmđộclập.

LSTM/CNN gốc thua persistence trên test khóa. Residual cải thiện rõ so với LSTM gốc nhưng chỉ nhỉnh nhẹ persistence trên test cũ đã quan sát; không phải holdout độc lập, chưa chứng minh thắng bền vững/ý nghĩa thống kê hoặc lợi nhuận. Không train/tune/refit thêm trong audit cuối.

Nguồn: `logs/audit/tv6_item5_20261126T172135216078Z/metrics.csv`, `logs/audit/tv6_lstm_completion_20261127T023617456097Z/metrics.csv`; bảngtổng `logs/audit/tv6_item10_20261128T032501868251Z/per_horizon.csv`.

---

## Lịch sử các giai đoạn — không dùng làm trạng thái hiện tại

# Kết quả so sánh baseline

TV5 mục9 đã có so sánh validation2023, chưa phải đánh giá test cuối. Cùng250 mẫu/ngày/scaler, CNN và LSTM một bước lookback30 với ba seeds42/123/456.

| Phương pháp | MAE USD | RMSE USD |
|---|---:|---:|
| Persistence | 1,6368 | 2,1206 |
| CNN mean ± std mẫu | 3,3660 ± 0,3065 | 4,3507 ± 0,3502 |
| LSTM mean ± std mẫu | 2,2494 ± 0,4520 | 2,7511 ± 0,4606 |

Persistence thấp hơn cả sáu model theo MAE/RMSE trên validation. LSTM trung bình thấp hơn CNN. Validation đã được dùng chọn checkpoint/lookback; không suy rộng thành test performance hoặc lợi nhuận. Ngân sách tìm kiếm LSTM/CNN khác nhau. [Chi tiết, từng seed và bằng chứng](audits/TV5_Item9_Validation_Comparison.md). Multi-step và đánh giá test cuối tiếp tục ở TV6, không coi báo cáo toàn project đã hoàn thành.

## Nội dung cần hoàn thiện

Điền bằng hoạt động thực tế trong đúng phạm vi Define/Design.

## Bằng chứng

Liên kết dataset version, run/release, logs, audit và phép kiểm tra liên quan khi có. Không điền số liệu giả hoặc kết luận trước thực nghiệm.
