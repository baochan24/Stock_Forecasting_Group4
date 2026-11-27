# TV5 — phạm vi cập nhật Git ngày26/11/2026

Theo yêu cầu người dùng, cập nhật nhánh TV5 từ baseline edc2bd953c7644040f4142a545316377cd143e13. Dùng checkout riêng, không stage/reset workspace chính hoặc sửa checkout Stock_Forecasting_Group4 lồng.

Source CNN và dependencies TV1–TV4, training/artifact/evaluation/monitoring, tests, cấu hình khóa, tài liệu và notebook canonical được lấy từ workspace đã nghiệm thu. README trạng thái đầu nhánh được cập nhật theo kết quả TV5. Trước push chạy lại162 tests từ checkout sắp publish, xác nhận imports thuộc checkout này.

.gitattributes giữ nguyên byte để Git không đổi EOL làm lệch SHA256 source/config/notebook đã ghi trong receipts và plan lock. Các bản artifacts đã đóng gói trước vẫn bất biến; cập nhật tài liệu giới thiệu/publication không thay số liệu hoặc mô hình.

## Dọn bản trùng và file không cần

Nhánh baseline chỉ có skeleton và model/tests CNN ban đầu, không có file trùng hoặc generated artifacts đủ căn cứ để xóa. Giữ README cấu trúc của các thành viên khác theo rule. Model/tests/README cũ được cập nhật tại chính đường dẫn canonical, không tạo bản model thứ hai. Mỗi TV chỉ publish notebook canonical, không đưa bản UPDATED, precision copies, __pycache__, snapshots, scaler, weights, logs, ZIP hoặc venv lên Git.

Notebook TV5 giữ output đã chạy và sơ đồ để xem trên GitHub. Dữ liệu mẫu/bảng tổng hợp và ảnh nhúng trong notebook là bằng chứng trình bày có chủ đích; không kèm datasets đầy đủ hoặc checkpoint. Artifacts được bàn giao riêng theo docs/TV5_Setup_and_Handoff.md, nguồn public Git đơn thuần chưa đủ Run All E2E.

Không merge main hoặc nhánh khác, không force-push và không thay lịch sử nhánh. Test cuối/API/production/máy người nhận vẫn chưa nghiệm thu trong lần publish này.
