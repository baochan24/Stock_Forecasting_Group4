# LSTM một bước: kiểm chứng thay cách đọc chuỗi

Hoàn thành local ngày 27/11/2026. **Không chọn mean readout để thay bản hiện tại:** độ chính xác không cải thiện nhất quán qua hai fold. Giữ nguyên ứng viên residual dùng last readout; catalog v1 và kết quả test không thay đổi.

## Thay đúng một yếu tố

Control: Linear(hidden cuối). Thử nghiệm: Linear(trung bình 30 hidden). Cùng LSTM một lớp hidden32, 4513 tham số, float64, khởi tạo core giống nhau theo seed, zero output head, relative input/delta target, scaler và mẫu train/validation của fold. Adam/MSE, lr0.001, batch32, shuffle chỉ train, max100/patience10 không đổi. Không thay feature, lookback, số lớp hoặc learning rate.

Sáu run mới: validation2022/2023 × seeds42/123/456. Control tái sử dụng sáu run residual last đã được pin và audit, không chọn checkpoint khác theo kết quả lần này. Mean checkpoint dùng best validation MSE, ghi history và reload từ file để kiểm tra output. Tổng79epoch,90,18giây ghi nhận cho CLI, không tính audit/notebook. Không chạy CNN/h5 hoặc testforward mới; đây là phát triển sau khi đã quan sát test, không phải đánh giá độc lập.

Plan: `experiments/configs/tv6_mean_readout_ablation_v1.json`. Class riêng `backend/models/lstm_one_step/mean_readout.py`; không sửa default class/model.py hoặc các run cũ. Sáu checkpoint mới mang purpose development, không được promote.

## Độ chính xác trên lịch sử thật

Mean ± sample std ba seed, đơn vị USD:

| Validation | Readout | MAE | RMSE |
|---|---|---:|---:|
| 2022 | Last — control | **2,596975 ± 0,004892** | **3,327008 ± 0,013750** |
| 2022 | Mean — thử nghiệm | 2,598652 ± 0,003098 | 3,339836 ± 0,002120 |
| 2023 | Last — control | 1,619409 ± 0,000959 | 2,106283 ± 0,000550 |
| 2023 | Mean — thử nghiệm | **1,617996 ± 0,000564** | **2,105788 ± 0,000470** |

Mean kém hơn cả MAE/RMSE ở2022; ở2023 chỉ giảm MAE khoảng0,001413USD vàRMSE0,000495USD. Không tuyên bố ý nghĩa thống kê hoặc ưu thế thực tiễn, không chọn riêng năm2023 để công bố thắng. Điều kiện xem xét cải thiện qua cả hai fold đã nêu trước chạy chưa được đáp ứng.

## Lịch sử thật so với các đối chứng

MAE mean ba seed:

| Fold/readout | Real | Flat | Đảo29giá trước | Xáo trộn29giá trước |
|---|---:|---:|---:|---:|
| 2022 Last | 2,596975 | 2,601771 | 2,694281 | 2,622649 |
| 2022 Mean | 2,598652 | 2,598910 | 2,598656 | 2,598653 |
| 2023 Last | 1,619409 | 1,619649 | 1,617603 | 1,618488 |
| 2023 Mean | 1,617996 | 1,619590 | 1,618033 | 1,618016 |

Mean có real tốt hơn flat một chút ở2023, nhưng độ nhạy với thứ tự prefix rất nhỏ trên cả hai năm. Không đủ khẳng định học động học chuỗi mạnh hơn; cũng không đủ kết luận mọi LSTM không dùng lịch sử. Flat/reverse/shuffle là input nhân tạo có thể ngoài phân phối, chỉ dùng chẩn đoán, không chọn làm input triển khai.

## Gradient tăng không tự làm dự báo tốt hơn

Ghi gradient trên bản sao ở các epoch1/5/10, cùng batch train middle32. Không thêm optimizerstep hay làm thay đổi model/RNG gốc. Tỷ lệ gradient tọa độrelativeinput cũ nhất/vị trí29 của mean readout khoảng0,81–1,56 trên các snapshot đã ghi, thay vì rất nhỏ như quan sát last checkpoint trước đó. Đây là snapshot ở thời điểm khác nhau, không là phép đối chiếu optimizer trajectory đầy đủ hoặc thước đo chất lượng dự báo.

Mean readout tạo đường ảnh hưởng trực tiếp từ các hidden sớm đến đầu ra, nhưng MAE/RMSE không tốt hơn nhất quán. Vì vậy, **chỉ làm gradient ở quá khứ mạnh hơn chưa đủ để sửa sai số trong thử nghiệm này**. Không suy ra tăng layers/epochs/lr hoặc ép mạng dùng đủ30phiên sẽ giúp ích.

## Quyết định và giới hạn

Không áp dụng thay đổi mean readout vào ứng viên chính, không tự mở thêm cấu hình trong lần thử này. Giữ last residual làm control và giữ kết quả xấu để báo cáo. Kết quả thu hẹp giả thuyết: độ nhạy thấp ở phiên cũ không thể được coi là nguyên nhân duy nhất rồi sửa chỉ bằng readout trung bình.

Nút thắt còn lại là tín hiệu dự báo hữu ích từ một chuỗi giá, mức điều chỉnh gần hằng số và tính ổn định qua giai đoạn. Nếu nghiên cứu tiếp, cần một giả thuyết kiểm chứng cụ thể và ngân sách rõ ràng; không thay nhiều yếu tố hoặc tiếp tục truy tìm điểm đẹp trên cùng validation. Không có bằng chứng độc lập mới cho candidate sau test, không có kết luận lợi nhuận giao dịch.

## Kiểm chứng và bàn giao

- Hai tests mới đạt: cùng tham số/khởi tạo, phép mean forward đúng, gradient đầu chuỗi và độc lập giữa mẫu; JUnit `logs/audit/tv6_readout_tests.xml`.
- Sáu run hoàn tất, đủ48metric rows/12.024prediction rows cho cả control và thử nghiệm, đủ bốn điều kiện/ba seed/hai fold. Audit độc lập đối chiếu full calendar keys, actual/origin snapshot, scalar MAE/RMSE, bestepoch và checkpoint/scale MSE, hashes không đổi.
- Receipt `logs/audit/tv6_readout_ablation_20261127T021734341342Z/summary.json`; audit độc lập, CSV/PNG vànotebook_verification cùngfolder. Checkpoints nằm dưới `artifacts/checkpoints/tv6_readout_ablation_20261127T021734341342Z/`.
- Notebook06 hiện34cells/17code cells có output thật, thêm bảng từngseed/mean/std/flat sensitivity, loss và loggradient. Builder đồng bộ, giữ nguyên30cells trước. Run All không train lại.
- CLI `scripts/run_tv6_readout_ablation.py`; tái kiểm không train bằng `scripts/audit_tv6_readout_ablation.py`. Chưa xác nhận trên máy thành viên khác.
