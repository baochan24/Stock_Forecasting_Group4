# TV6 mục4 — nghiệm thu evaluation USD/alignment/horizon

Ngày27/11/2026 theo múi giờAsia/Bangkok. Bám protocol v1, không đổi models/data/seed/demo rule hoặc tính performance test. Kiểm từ số liệu tính tay đến toàn bộ validation đã có ở mục3.

## Đầu ra

Module forecast_records kiểm full groups/3seeds, source context và exact ordered keys trước khi ghép actual. Tái dùng one_step math, per-horizon/overall/std theo protocol, baseline riêng. Mô tả đầy đủ docs/TV6_Evaluation_Contract.md. Các quyết định mẫu/cohort/metric không đổi, chỉ hoàn thiện implementation.

101/101 tests đạt, gồm32 tests mới của evaluator và69 tests inference/protocol/evaluation trước đó. Tính tay kiểm MAE,std ddof1, h5 overall sqrt(mean squares) khác mean horizon RMSE, count windows/errors; fail missing/duplicate/reorder/ID/date/seed/run/model/protocol/units/mode/split/baseline identity/nonfinite/overflow. Có positive/negative full-cohort tests bằng fixture tổng hợp2024, không phải đánh giá held-out stock.

Lượt đầu97 tests đạt, sau hoàn thiện output overall dùng horizon_step=None và thêm single-mode/full-cohort fixtures đã chạy lại101. Không dùng receipt cũ thay chứng nhận cuối. JUnit logs/audit/tv6_item4_tests.xml.

## Validation thật

31 metric rows,8 aggregate rows,6.670 joined residual rows từ predictions input-only mục3 và raw target JSON validation. H1 khớp metric TV5 trong1e-12; baseline đúng rawlast, cùng250 mẫu. H5 dùng246 windows, từng horizon246 errors, overall1.230 errors mỗi run nhưng vẫn246 windows. Cả3 seed được báo, không chọn seed thắng.

| Validation | MAE USD | RMSE USD |
|---|---:|---:|
| H1 LSTM mean3seed | 2,249421 | 2,751112 |
| H1 CNN mean3seed | 3,366034 | 4,350735 |
| H1 persistence | 1,636779 | 2,120593 |
| H5 LSTM overall mean3seed | 3,434674 | 4,261446 |
| H5 persistence overall | 2,984996 | 3,903600 |

Bảng chỉ minh họa làm tròn, CSV giữ precision; không dùng số hiển thị để tính tiếp. H5 model và population khác h1, không kết luận chỉ từ so cột giữa hai nhiệm vụ. Full table có persistence h5/từng horizon và std ở notebook/CSV.

Receipt logs/audit/tv6_item4_20261126T170304891907Z/summary.json (UTC26/11, local27/11), metrics.csv,aggregates.csv,residuals.csv cùng thư mục. Source/artifacts/protocol được kiểm trước/sau, không sửa checkpoint/scaler hoặc train/inference mới. Notebook06 có bảng từng run/horizon, aggregate,residual mẫu và4 panels validation, giữ output các mục cũ.

Notebook thực thi đủ6/6 code cell, tổng12 cells. Kiểm độc lập thêm từng seed h5 cho (RMSE_USD/scaler.scale)^2 khớp validation_mse TV4 trong rtol1e-12/atol1e-14, không tính lại test; independent_verification.json cùng thư mục. Bản h5 overall không có horizon_step, không tạo nhầm horizon0.

## Giới hạn và tiếp theo

Kết quả validation đã dùng chọn checkpoint, không là final test. Hàm evaluation cần caller xác minh actual source, không chỉ tin labels metadata. Protocol lock/checksums không thay xác thực dữ liệu bên ngoài. Chưa release/API/selected-range UI hoặc inference test workflow. Mục5 tiếp theo sẽ tích hợp đường final evaluation trên test theo protocol, trước khi chạy cần kiểm lại readiness và logging; không tự bật từ mục4.
