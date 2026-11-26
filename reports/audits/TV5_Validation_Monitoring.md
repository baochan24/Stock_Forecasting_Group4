# TV5 — bổ sung monitoring sau train

Ngày26/11/2026, theo yêu cầu bổ sung monitoring. Phạm vi là kết quả validation2023 đã có, 250 target dates, ba CNN/ba LSTM và persistence. Không train lại, không đổi mô hình/checkpoint, không đánh giá test hoặc production.

## Đầu ra

- Signed residual theo ngày, tách ba phương pháp và hiển thị mọi seed. Dương là dự báo cao hơn actual.
- MAE trượt20 phiên, cửa sổ chỉ kết thúc tại ngày đang xét, 19 phiên đầu để NaN và231 cửa sổ đầy đủ mỗi run. Dùng phiên dataset, không phải20 ngày lịch.
- Histogram residual dùng chung bins, riêng từng seed, không coi các residual giữa seed là mẫu độc lập.
- MAE theo tháng trung bình metric từng seed, không phải metric của dự đoán ensemble.
- Bảng bias, P95/max absolute error, tỷ lệ dự báo cao, tỷ trọng squared error của5 lỗi lớn nhất, top10 errors từng run. Notebook hiển thị top2/run, CSV giữ đủ70 hàng top10.
- Inventory loss/finite guards/checkpoint/CPU/inference telemetry, phân biệt những gì chưa đo.

MAE/RMSE và rolling/monthly metrics gọi module evaluation chung. Kiểm tất cả methods cùng ordered IDs/ngày/actual và residual đúng predicted-actual; không tự loại mẫu hoặc sắp xếp lại để che lệch input. Metrics tính lại khớp bảng mục9 trong dung sai1e-12. Giữ nguyên input dataframe và predictions nguồn.

## Quan sát thực tế

CNN có P95 absolute error khoảng8,37–9,92USD, LSTM4,45–6,05USD, persistence4,16USD. Max absolute error CNN11,67–13,42USD, baseline9,04USD. Điều này cung cấp bằng chứng mô tả rằng tail errors của CNN lớn hơn, phù hợp RMSE cao; chưa chứng minh nguyên nhân từ convolution/pooling hoặc overfit.

Bias CNN tùy seed khoảng−0,285 đến+0,237USD, LSTM seed456 khoảng−0,910USD. Bias nhỏ không đồng nghĩa MAE nhỏ vì lỗi dương/âm có thể bù nhau. Top5 squared-error share CNN12,4–15,3%, không nên quy toàn bộ sai số CNN cho vài phiên duy nhất. Không tuning sau phân tích này.

## Kiểm chứng và lưu trữ

17/17 tests evaluation/monitoring đạt, gồm5 tests mới kiểm cửa sổ không dùng tương lai, không mutate và từ chối residual/ngày/mẫu/actual không nhất quán. JUnit logs/audit/tv5_monitoring_tests.xml. Phân tích thực trên7 runs đạt, nguồn CSV và source giữ hash trong lúc chạy.

Receipt logs/audit/tv5_monitoring_20261126T091236219563Z/summary.json, cùng summary.csv, rolling.csv, monthly.csv, largest.csv và bốn PNG. Notebook05 có25 cells,14/14 code cell lưu output, thêm4 ảnh và giữ outputs các mục trước; notebook_verification.json cùng thư mục.

## Giới hạn monitoring

Train/validation loss, early stopping, finite guards, model/source identity và reload đã có bằng chứng các mục trước. CNN runner wall/CPU time và inference local có số đo. Peak RAM lịch sử chưa được thu, không tái dựng hồi tố hoặc dùng RAM inference thay RAM training. Chưa có live TensorBoard CNN, automatic alerting hoặc production drift telemetry; model chưa triển khai. Đây là monitoring thực nghiệm/validation, không chứng nhận monitoring toàn hệ thống.

Không chạy lại official training chỉ để thêm biểu đồ. Nếu tương lai cần peak RAM, phải đo ở run mới và gắn run ID mới, tách kết quả lịch sử. Mục10 audit/tái lập/bàn giao vẫn là hạng mục kế tiếp, không đánh dấu hoàn thành từ phần bổ sung này.
