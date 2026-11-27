# TV6 — audit lại đánh giá và độ phủ dữ liệu

Ngày27/11/2026. Theo yêu cầu kiểm còn sai sót/thiếu dữ liệu, audit cả code và kết quả validation thật, không chạy held-out test hoặc train/tuning lại.

## Phát hiện thật và sửa

Evaluator đã kiểm prediction/actual cùng keys nhưng validation chưa đối chiếu cohort độc lập. Nếu caller cùng bỏ một sample khỏi mọi prediction và actual, vẫn có thể nhận validation_full_set. Đây là lỗi guard tái sử dụng, chưa phải sai điểm số đã báo vì CLI hiện dùng đủ raw source và đã kiểm counts.

Đã thêm load_validation_cohorts đọc input/target JSON có hashes trong protocol, bắt expected_validation_cohorts cho full validation. Cả số mẫu và ordered-key hash phải khớp source độc lập, thiếu/lệch cả hai phía vẫn bị từ chối. Không derive reference từ data đã lọc, không đổi protocol v1 hay tạo score từ subset rồi gọi full-set.

104/104 tests inference/protocol/evaluation đạt, gồm3 regression mới: cùng thiếu sample ở hai phía, không có cohort reference và source checksum sai. So với101 tests trước, chỉ siết guard. Receipt JUnit logs/audit/tv6_item4_audit_tests.xml. Validation tái tính tại logs/audit/tv6_item4_20261126T171056822137Z/summary.json, metrics/aggregates/residuals cùng thư mục. Điểm số cũ không đổi trong1e-12.

## Kiểm độc lập trên dữ liệu thật

scripts/audit_tv6_evaluation.py xác nhận6.670 actual khớp adjusted_close snapshot theo target_date, baseline khớp giá tại forecast_origin, signed residual đúng predicted-actual. Tính lại31 MAE/RMSE bằng math.fsum/sqrt,8 aggregates bằng statistics.mean/stdev, count windows/errors đều đúng. Không gọi lại module metric để tự so implementation với chính nó.

H1 phủ đủ250 target dates2023, không mất30 phiên đầu validation. H5 có246 windows với5 targets cùng split.4 ngày bắt đầu target26/27/28/29-12-2023 bị loại vì cửa sổ5 phiên sẽ chạm2024, không phải lỗi làm mất dữ liệu. Horizon1 và5 có ngày đầu/cuối lệch4 phiên đúng thiết kế; N×5 residuals có ngày actual lặp giữa các origins nhưng khóa forecast khác nhau, không phải duplicate lỗi. Không coi các residual này là observations độc lập khi suy luận thống kê.

Receipt audit logs/audit/tv6_evaluation_audit_20261126T171231516396Z/summary.json. So sánh31 metric rows với kết quả trước sửa giữ nguyên. Source/data/model/protocol không bị thay để cải thiện metric.

## Những gì chưa đánh giá

- Test2024–2025 thực chưa chạy, đúng flow mục5; hiện chưa nghiệm thu khả năng tổng quát hóa cuối.
- Phân tích lỗi test/giai đoạn/horizon/phiên biến động lớn thuộc mục6. Validation đã có monitoring h1 và metric h5, không thay thế phân tích test.
- Snapshot không có2026/live/intraday; OHLCV không là input của thiết kế một feature adjusted_close. Đây là giới hạn đã chốt, không âm thầm thêm features/data để tuning.
- MAE/RMSE không chứng minh lợi nhuận/khả năng giao dịch;3 seed/std không là confidence interval hoặc significance test. Adjustment hồi cứu, nguồn dữ liệu và ngân sách tìm cấu hình khác nhau vẫn là giới hạn.

Kết luận mục4 đủ nghiệm thu công cụ đánh giá/validation sau sửa guard, chưa thể kết luận toàn bộ model evaluation đã hoàn thành. Tiếp theo mục5 theo protocol đã khóa.
