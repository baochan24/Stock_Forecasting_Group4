# TV5 mục9 — so sánh CNN/LSTM/persistence trên validation

Ngày26/11/2026. Cùng250 sample IDs/ngày target năm2023, cùng snapshot/scaler/prepared/lookback30/common-history. Dùng ba best validation checkpoint mỗi mạng theo seeds42/123/456. Không train, tuning hoặc chọn seed mới. Không đánh giá hiệu năng test2024–2025; final evaluation thuộc flow TV6.

## Thực hiện và kiểm chứng

Workspace chưa có module metric/persistence chung. Bổ sung dependency tối thiểu ở backend/evaluation/one_step.py và backend/baselines/persistence.py, không viết metric riêng trong notebook/script. Mười hai tests tính tay MAE3/RMSE√10, last raw price h1/h5, từ chối lệch thứ tự/ngày/thiếu/trùng mẫu, shape và NaN/Inf đã đạt. JUnit logs/audit/tv5_item9_metric_tests.xml. Không coi phần này là hoàn thành TV6.

Script compare_tv5_validation.py xác minh lock CNN, loader/provenance/scaler fit train, raw target JSON và inverse target khớp. Baseline tính trực tiếp từ raw input JSON, kiểm bằng inverse input; không lấy y làm baseline. Nạp checkpoint bằng expected identities, CNN thêm fingerprint/run/seed; LSTM đối chiếu metadata data/config/run/seed, mode một bước. MSE chuẩn hóa inference phải khớp kết quả train đã ghi. Cả hai mạng chạy cùng loader theo đúng ordered IDs/ngày. Source và hashes checkpoint được ghi audit.

Đưa predictions về USD bằng inverse_scale/scaler hiện có, không fit hoặc làm tròn trước metric. Báo từng seed và mean/std ddof1, baseline deterministic chỉ một kết quả không giả lập ba run. Không dùng mean prediction thành ensemble.

## Giới hạn

Validation đã dùng để chọn best epoch và lookback LSTM, vì vậy số liệu không đại diện holdout test cuối. LSTM chọn lookback từ10/30/60, CNN chỉ kiến trúc A, search budgets khác nhau. Không khẳng định khác biệt có ý nghĩa thống kê chỉ từ ba seeds.

Thời gian train lịch sử được giữ để mô tả, chạy ở thời điểm khác nên không là controlled speed benchmark. Inference đo lại cùng CPU/thread/data, warmup và20 lượt, median từng seed; networks gồm DataLoader, persistence gồm dựng mảng input, không suy ra kernel speed hoặc production latency. Chưa đo peak RAM.

## Kết quả thực tế — validation2023

| Phương pháp | MAE USD | RMSE USD |
|---|---:|---:|
| Persistence deterministic | 1,6367788085937487 | 2,120592871143024 |
| CNN mean ± std 3 seed | 3,3660344434708 ± 0,30654699465954516 | 4,3507353552455195 ± 0,3501760819117245 |
| LSTM mean ± std 3 seed | 2,2494206675196757 ± 0,45203240672016887 | 2,7511123408512077 ± 0,4605560813665601 |

Cả ba seed từng mạng đều có MAE/RMSE lớn hơn persistence trên validation này. LSTM có sai số trung bình thấp hơn CNN. Không chứng minh model sâu vượt baseline, không chuyển kết quả thành khẳng định test hoặc lợi nhuận. Không train/tuning lại sau nhìn kết quả.

Từng seed CNN42/123/456 có MAE3,456691/3,024384/3,617029 và RMSE4,573323/3,947099/4,531784. LSTM42/123/456 có MAE1,908008/2,078204/2,762050 và RMSE2,410920/2,567211/3,275205. CSV giữ precision đầy đủ, bảng diễn giải không dùng làm đầu vào tính metric.

Inference median từng seed được đo lại local với20 lượt và một Torch thread, CNN khoảng7,19/8,87/14,68 ms, LSTM29,13/27,73/15,62 ms mỗi250 mẫu, persistence1,54 ms. Dùng giới hạn timing đã nêu, không kết luận speedup kiểm soát từ các số này. Params CNN17.057, LSTM4.513; official epochs CNN146, LSTM lookback30 tổng285, ngoài ra TV4 đã có sáu run lookback10/60 để lựa chọn.

Receipt `logs/audit/tv5_item9_20261126T045347179803Z/summary.json`; metrics.csv, predictions_usd.csv, comparison_overview.png và notebook_verification.json cùng thư mục. Nạp/kiểm đủ sáu checkpoints, MSE chuẩn hóa khớp kết quả train, raw/inverse target và baseline khớp, source giữ hash trong quá trình chạy. Notebook05 có23 cells và13/13 code cell lưu output, giữ kết quả mục trước.

Mục9 đạt phạm vi so sánh validation local. Mục10 tiếp theo là audit/tái lập/bàn giao TV5, chưa thực hiện trong mục9. Test cuối vẫn chưa được đánh giá hiệu năng.
