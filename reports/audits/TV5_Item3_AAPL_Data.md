# TV5 mục 3 — dữ liệu AAPL cho CNN

Ngày 26/11/2026. Consumer tại backend/experiments/runner/cnn_data.py dùng lại factory dữ liệu TV4 và reference one-step lookback30/common60 đã train. Preprocessing, scaler và artifacts nguồn giữ nguyên.

## Kiểm chứng dữ liệu

| Tập | Mẫu | Batch | Batch cuối | Ngày target |
|---|---:|---:|---:|---|
| Train | 1.954 | 62 | 2 | 31/03/2015–30/12/2022 |
| Validation | 250 | 8 | 26 | 03/01/2023–29/12/2023 |

Input (B,30,1), target (B,1), CPU float64. Các ngày đủ lịch sử 60 phiên được dùng làm tập target chung để so lookback của LSTM, cửa sổ CNN vẫn gồm 30 phiên. Mẫu validation đầu dùng origin 30/12/2022 để dự báo phiên 03/01/2023.

Đã đối chiếu cấu hình dữ liệu với metadata run LSTM lookback30 seed42, giữ cùng version, prepared/scaler ID và hash manifest. Factory kiểm snapshot, năm hash nguồn, thống kê scaler fit train và coverage cửa sổ. Script đối chiếu từng tensor X/y với NPZ, từng ID và ngày với record JSON theo đúng thứ tự, ghi hash danh sách ID.

CNN chỉ nhận X, transpose bên trong model. Forward toàn bộ 70 batch bằng model khởi tạo ở eval/inference mode, output hữu hạn và đúng shape target. X/y không đổi sau forward. Mỗi origin trước ngày target. Lượt này không huấn luyện hoặc tính metric chất lượng dự báo.

[Receipt dữ liệu và ví dụ mẫu](../../logs/audit/tv5_item3_20261126T034224769679Z/summary.json)

## Hồi quy và notebook

Bộ kiểm tra CNN và training đạt 98/98 tests, gồm ba ca mới từ chối reference lookback/horizon/common-history lệch phép so sánh. [JUnit](../../logs/audit/tv5_item3_regression_20261126.xml)

Notebook 05 chạy 5/5 code cell, có bảng số mẫu/ngày/batch, ví dụ input chuẩn hóa/target và provenance thật. [Receipt thực thi](../../logs/audit/member_notebooks_20261126T034133738444Z/summary.json)

Phần nối model factory, optimizer và checkpoint CNN tiếp tục ở các mục 5/6. Mục tiếp theo là 4, kiểm sâu cấu hình/model, gradients, Adam update, dropout và state_dict lưu/nạp.
