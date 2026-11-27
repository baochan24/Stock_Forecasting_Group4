# Technical Risks

Đây là rủi ro dự kiến, chưa phải lỗi đã xảy ra. Chưa gán xác suất thiếu căn cứ.

| Rủi ro | Kiểm soát/bằng chứng dự kiến |
|---|---|
| Dữ liệu tải khác nhau | Snapshot/hash/chính sách tải; đối chiếu số dòng và khoảng ngày |
| Giá điều chỉnh hồi cứu | Ghi giới hạn point-in-time trong metadata/báo cáo |
| Rò rỉ dữ liệu | Audit fit scaler, ngày input/target, validation/test |
| Sai window/shape/ngày | Đối chiếu mẫu một/năm bước và shape bằng tay |
| NaN/Inf, overfit, seed biến động | Loss logs, kiểm tra hữu hạn, early stopping, nhiều seed |
| CPU/RAM vượt ngân sách | Chạy ngắn, đo epoch/inference/RAM trước mở rộng |
| So sánh thiếu công bằng | Cùng tập mẫu, quy tắc validation, ngân sách công bố |
| Metric/multi-step sai | Tính lại từ prediction, tách horizon, không trung bình RMSE batch |
| Trộn model/scaler/dataset | Kiểm tra bộ release tương thích khi nạp |
| API/front-end lệch kết quả | Kiểm tra request tới UI, ngày/đơn vị/release |
| Trace giải thích sai | Đối chiếu phép tính; gắn nhãn minh họa |
| Không chạy máy khác | Dependencies và hướng dẫn; thành viên khác chạy thử |
| LSTM không thắng baseline | Giữ giả thuyết trung lập và báo cáo trung thực |
| Phạm vi quá rộng | Ưu tiên pipeline và yêu cầu đề trước giao diện sâu |

Mỗi rủi ro bổ sung chủ sở hữu, trạng thái, bằng chứng, hành động khi triển khai. LSTM không thắng không tự nghĩa pipeline lỗi. Kết quả đẹp không chứng minh pipeline đúng.
