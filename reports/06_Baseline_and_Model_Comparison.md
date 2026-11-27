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
