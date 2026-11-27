# TV6 mục 5 — đánh giá test chính thức

Hoàn thành local ngày 27/11/2026 (Asia/Bangkok). Giữ nguyên protocol v1, 9 checkpoint chọn bằng validation, scaler train và seeds42/123/456. Không huấn luyện lại, không tuning/chọn seed theo test.

## Phạm vi và kết quả

Test2024–2025: một bước502 mẫu; năm bước498 cửa sổ,2490 sai số mỗi model/baseline. Inference nhận input riêng; target được đọc sau dự đoán từng chế độ. CPU float64, một thread, batch32 giữ batch cuối. Lịch sử đã quan sát được cập nhật theo origin; weights/scaler cố định. H5 là direct output, không recursive.

| Task/method | MAE USD | RMSE USD |
|---|---:|---:|
| H1 persistence | 2.476989 | 3.654583 |
| H1 LSTM, mean ± sample std | 10.896342 ± 1.604931 | 14.031708 ± 1.741287 |
| H1 CNN, mean ± sample std | 8.162562 ± 0.965098 | 10.073087 ± 1.111229 |
| H5 persistence overall | 4.632497 | 6.707243 |
| H5 LSTM overall, mean ± sample std | 12.603942 ± 0.223053 | 16.155448 ± 0.319645 |

Persistence thấp lỗi hơn mọi seed của mô hình trên cohort tương ứng. CNN h1 thấp lỗi hơn LSTM h1 trong cấu hình đã khóa; không chứng minh ưu thế kiến trúc tổng quát vì ngân sách tìm kiếm khác nhau. Kết quả không đạt mục tiêu vượt baseline, nhưng là kết quả thực nghiệm hợp lệ để báo cáo. Không tuning sau khi thấy test rồi coi cùng test là chưa quan sát.

H5 overall gộp498×5 lỗi trước MAE/RMSE; không lấy trung bình5 RMSE. Từng horizon và từng seed có đủ trong CSV/notebook. Hai task dùng cohort khác nhau, không so trực tiếp như cùng bài toán.

## Kiểm chứng và bằng chứng

- 104 regression inference/evaluation/protocol đạt; 2 tests vòng đời context/path đạt. JUnit: `logs/audit/tv6_item5_readiness_tests.xml`, `tv6_item5_context_tests.xml`.
- Receipt: `logs/audit/tv6_item5_20261126T172135216078Z/summary.json`; UTC filename tương ứng ngày27/11 tại Bangkok. `execution.json` ghi running trước test forward, completed sau kiểm tra.
- 13.474 predictions/residuals,31 metrics,8 aggregates; đủ9 models. Kiểm tra hash120 artifacts cùng source/protocol/registry trước/sau, model eval/frozen/no-grad.
- `scripts/audit_tv6_test_results.py` đối chiếu actual theo ngày snapshot, persistence theo origin và mean/std độc lập bằng statistics. Đạt; sai khác serialization actual tối đa cỡ2.84e-14USD, kiểm với atol1e-12USD, không làm tròn trước metric.
- Metric từng run/horizon được kiểm bằng scalar math.fsum/sqrt. Aggregate ddof1, không ensemble.
- Notebook06 hiện16 cells,8 code cells có output, thêm bảng31 metrics/8 aggregates và biểu đồ hai panel. Giữ output các mục cũ; builder đồng bộ. Cell mục5 không chạy lại test, chỉ đọc và xác minh kết quả đã lưu.

## Thay đổi và giới hạn

`FrozenForecaster` mặc định vẫn chỉ validation; test yêu cầu ledger đang running đúng protocol trong thư mục item5. Đây là guard quy trình local, không phải cơ chế xác thực chống người có quyền sửa workspace. Receipt/source hashes mục3 là bằng chứng phiên bản lịch sử; mục5 mở đường chạy test có chủ đích, không tuyên bố source inference hiện còn giống mục3.

Chưa nghiệm thu máy khác. Không suy kết quả thành lợi nhuận giao dịch; adjusted prices hồi cứu không phải point-in-time, h5 windows chồng lấn không độc lập. Nguyên nhân lỗi cao và phân tích theo thời gian thuộc mục6, chưa kết luận nguyên nhân ở đây. Release/API/frontend còn mục7–9.

Lệnh tái kiểm không forward: `.venv/tv4_clean/Scripts/python.exe scripts/audit_tv6_test_results.py`. CLI thực thi `scripts/evaluate_tv6_test.py` tạo run ledger mới mỗi lần; không cần chạy lại để xem notebook, không thay cấu hình theo test.
