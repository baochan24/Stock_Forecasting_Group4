# Kiểm lại vì sao persistence thắng trên test

Ngày27/11/2026. Phân tích mô tả sau test, không train/tune/forward mới. CLI `scripts/analyze_tv6_test_gap.py`; bằng chứng `logs/audit/tv6_item5_20261126T172135216078Z/gap_diagnosis/`.

## Kết luận có bằng chứng

**Mô hình có sai lệch giảm giá có hệ thống và lỗi tăng rõ khi origin vượt mức giá tối đa train. Persistence giữ đúng mức giá mới nhất, tránh phần điều chỉnh sai này.** Kết quả phù hợp với hạn chế tổng quát hóa/ngoại suy mức giá; chưa đủ để xác định cơ chế nhân quả duy nhất.

Train2015–2022 có giá20,53–177,65USD, trung bình70,09; validation2023 có giá122,73–195,58, trung bình169,92; test2024–2025 có giá163,10–285,20, trung bình218,00.91,04% giá test cao hơn mức tối đa train. Với phân nhóm chỉ theo origin (không dùng actual tương lai để chọn nhóm),457/502 origin vượt mức tối đa train;45 còn lại trong miền train. Một cửa sổ origin trong miền vẫn có thể chứa lịch sử ngoài miền, nên đây không phải phân loại toàn bộ input in/out-of-distribution.

| Một bước, MAE USD | 45 origin không vượt train max | 457 origin vượt train max |
|---|---:|---:|
| Persistence | 2,759 | 2,449 |
| LSTM, trung bình3seed | 2,995 | 11,674 |
| CNN, trung bình3seed | 2,939 | 8,677 |

Baseline không xấu đi trên nhóm origin cao, trong khi lỗi mạng tăng rõ. Do đó giải thích đơn giản “test biến động mạnh hơn nên tất cả đều lỗi cao” không đủ; phần lỗi tăng riêng của mạng cần chú ý. Nhóm không cân bằng45/457 và có khác biệt thời gian, xu hướng, volatility, lịch sử; không suy bảng này thành thí nghiệm nhân quả.

LSTM h1 có bias(pred−actual) từ−9,10 đến−12,29USD, underprediction85,1–92,6% tùyseed. CNN bias−5,85 đến−7,77USD, underprediction81,1–86,3%. Trong khi actual−origin trung bình chỉ+0,161USD, mạng dự báo thay đổi trung bình khoảng−8,94 đến−12,13USD(LSTM),−5,69 đến−7,61USD(CNN). Đây là mô tả trung bình; không có nghĩa giá không có các phiên giảm mạnh.

## Vì sao phần điều chỉnh làm lỗi tăng

Đặt Δ=actual−origin, a=prediction−origin. MSE(model)=E[Δ²]+E[a²]−2E[aΔ]. Persistence cóa=0 nên MSE=E[Δ²]. Script kiểm đẳng thức cho mọi seed/segment/mode. H1 persistence MSE13,356USD²; phần E[a²] của LSTM145,824–240,328USD² và CNN63,547–104,034USD². Term−2E[aΔ] còn dương trên cả6 neural runs: phần điều chỉnh không bù được chi phí mà làm tổng lỗi tăng. Đây là phân rã chính xác của lỗi đã quan sát, không chứng minh nguyên nhân học ra weights.

## Đối chiếu source và các giải thích chưa được chứng minh

- LSTM `backend/models/lstm_one_step/model.py` dùng Linear(last hidden) dự báo mức giá chuẩn hóa; CNN dùng Conv/ReLU/MLP dự báo mức giá. Cả hai không buộc output bám last price bằng residual skip. Đây là thiết kế hợp lệ, nhưng không đảm bảo ngoại suy đồng nhất theo mức giá. Chưa làm ablation để chứng minh residual target/return target sẽ sửa được lỗi.
- StandardScaler chỉ affine transform/inverse, không clip về miền train. Giá vượt train vẫn được giữ; không có bằng chứng scaler “chặn giá”. Không tự refit scaler test.
- Các cổng LSTM có hoạt hóa bị chặn không có nghĩa output Linear bị chặn trong giá train; chưa đo gate saturation, không kết luận cơ chế này gây lỗi.
- Validation đã có34,4% giá vượt train max; pipeline một bước đã thua persistence ở validation. Vấn đề không chỉ xuất hiện khi mở test. Hiệu năng validation không chứng minh khả năng ngoại suy đến285USD.
- LSTM h1seed456 có dấu hiệu train tiếp làm validation xấu đi saubest75, nhưng đã restorebest. Không đủ quy toàn bộ kết quả cho overfitting. Train loss online và val loss eval không phải hai risk tính cùng weights/mode; chưa đánh giá train cố định cho kết luận định lượng overfitting.
- Tái kiểm snapshot actual, baseline origin, metric/aggregate/sourcehash đạt bằng script audit. Chưa tìm thấy lỗi ghép ngày, sai USD, thiếu seed/cohort trong bằng chứng hiện tại. Điều này không chứng minh toàn bộ hệ thống tuyệt đối không lỗi.

## Giới hạn và bước tiếp

Đây là kiểm tra nguyên nhân trọng tâm trong phạm vi phân tích lỗiTV6, chưa đánh dấu toàn bộ mục6 hoàn thành. Chưa phân tích đầy đủ outlier/event/yearly residual/horizon drivers hoặc kết luận causality. Không đổi checkpoint/scaler/cấu hình sau khi thấy test. Nếu nghiên cứu thay đổi mô hình cần quy trình phát triển/validation và tập kiểm chứng tương lai thích hợp; kết quả hiện tại phải giữ nguyên.

Notebook06 được thêm cell phân phối giá, bias từngseed và biểu đồ phân nhóm origin; kết quả thật đã lưu. Không phát sinh inference test mới.
