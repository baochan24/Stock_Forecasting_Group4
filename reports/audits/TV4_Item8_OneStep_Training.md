# TV4 mục 8 — kết quả LSTM một bước

## Audit sau training trước mục 9

Đã kiểm tra lại chín trạng thái completed, số epoch CSV, best epoch theo minimum validation loss, metadata checkpoint và SHA256 weights. Mọi giá trị train/validation loss và thời gian trong CSV đều hữu hạn. Cả chín run đạt đối chiếu. Cấu hình mục 9 đã xác nhận lookback 30, forecast_length 5, hidden 32, ba seed 42/123/456, Adam 0,001, batch 32, MSE, max_epochs 100, patience 10, clipping tắt và một luồng CPU.

Bốn run chạm giới hạn 100 epoch gồm lookback 10 seed 123, lookback 30 seeds 42/123 và lookback 60 seed 123. Hai run lookback 10/60 seed 123 có best ngay epoch 100. Các run này chưa đủ cơ sở để tuyên bố hội tụ. Giữ ngân sách đã chốt để bảo toàn phép so sánh giữa cấu hình.

Validation loss tăng cuối một số run, đặc biệt lookback 30 seed 123. Model đã chọn từ epoch tốt nhất và kiểm nạp lại ở mục 8. Chưa có bằng chứng buộc đổi learning rate, bật clipping hoặc tăng epoch cho mục 9. Những biến động cần được trình bày cùng độ lệch chuẩn và đường loss.

Kiểm tra lại dữ liệu thật cho LSTM năm bước đạt, gồm nguồn artifacts, shape, dtype, ID và ngày target, toàn bộ batch train/validation. [Biên bản dữ liệu mục 9](../../logs/audit/tv4_item3_20261125T133741337837Z/summary.json)

Kết luận pipeline đủ điều kiện tiếp tục mục 9 với model khởi tạo mới, checkpoint riêng và cấu hình năm bước đã chốt. Khi chạy cần lưu MSE tổng cùng từng horizon 1–5, xác minh reload trên toàn validation và cập nhật TensorBoard sau khi hoàn tất. Tập test dành cho giai đoạn đánh giá sau khóa cấu hình. Đánh giá MAE/RMSE USD và persistence/CNN còn thuộc phần việc sau.

Ngày 25/11/2026. Đã hoàn tất chín run theo kế hoạch mục 7, lookback 10/30/60 và seeds 42/123/456. Tất cả dùng cùng 1.954 mẫu train và 250 mẫu validation, CPU float64, một luồng tính toán, hidden 32, Adam 0,001, batch 32, tối đa 100 epoch và patience 10. Giữ scaler TV2 đã fit train.

## Kết quả validation

| Lookback | MSE trung bình ba seed | Độ lệch chuẩn mẫu |
|---|---:|---:|
| 10 | 0,012245378 | 0,016262211 |
| 30 | 0,003265939 | 0,001118952 |
| 60 | 0,003563105 | 0,000768613 |

Chọn lookback 30 theo MSE trung bình thấp nhất, đúng quy tắc đã chốt. Cả ba checkpoint theo seed vẫn được giữ để đánh giá sau. Các số trên dùng giá chuẩn hóa.

| Lookback | Seed | Best epoch | Epoch kết thúc | Validation MSE |
|---|---:|---:|---:|---:|
| 10 | 42 | 79 | 89 | 0,002993068 |
| 10 | 123 | 100 | 100 | 0,002720365 |
| 10 | 456 | 8 | 18 | 0,031022701 |
| 30 | 42 | 97 | 100 | 0,002462169 |
| 30 | 123 | 97 | 100 | 0,002791742 |
| 30 | 456 | 75 | 85 | 0,004543905 |
| 60 | 42 | 84 | 94 | 0,002814750 |
| 60 | 123 | 100 | 100 | 0,003524077 |
| 60 | 456 | 79 | 89 | 0,004350489 |

Lookback 10 biến động mạnh giữa seed, đặc biệt seed 456. Lookback 60 có độ lệch chuẩn nhỏ hơn 30 trong ba lần chạy này, trong khi 30 đạt trung bình thấp nhất. Những run kết thúc ở 100 epoch đã chạm ngân sách định trước. Kết quả chưa chứng minh hội tụ hoàn toàn.

## Kiểm chứng và bằng chứng

Mỗi best checkpoint được nạp vào instance mới và đo MSE trên toàn bộ validation, đối chiếu best_val_loss với dung sai tương đối 1e-12. Best epoch được đối chiếu với minimum của lịch sử. Các run dừng sớm kết thúc đúng 10 epoch sau best. Chín run đều hoàn tất, tổng 775 epoch. Tổng thời gian trainer khoảng 1.266,994 giây, tương đương 21,12 phút, có bao gồm xử lý checkpoint trong trainer. Tổng thời gian toàn đợt còn gồm xác minh dữ liệu và reload.

YAML thực thi, CSV từng epoch và metadata chứa seed, số luồng, cấu hình, hash backend/YAML và provenance. Hash entrypoint được lưu riêng. [Summary chín run](../../logs/audit/tv4_item8_20261125T122649342552Z/summary.json) · [Hash script thực thi](../../logs/audit/tv4_item8_20261125T122649342552Z/entrypoint_sha256.json)

Notebook 04 mục 8 có bảng từng seed, bảng trung bình/std và chín biểu đồ train/validation với mốc best epoch. [Hình các đường học](../../logs/audit/tv4_item8_20261125T122649342552Z/learning_curves.png)

Các kết quả này chọn cấu hình trên validation 2023. Test 2024–2025 và so sánh persistence/CNN thuộc quy trình đánh giá sau. Mục 9 tiếp theo huấn luyện LSTM năm bước tại lookback 30 với ba seed theo kế hoạch.
