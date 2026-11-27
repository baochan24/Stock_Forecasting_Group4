# Milestones

| Mốc | Sản phẩm | Điều kiện kiểm tra |
|---|---|---|
| M0 | Thiết kế | Define/design/folder structure nhất quán; việc mở được ghi |
| M1 | Dữ liệu và baseline | Snapshot, scaler, cửa sổ 1/5, persistence; đối chiếu tay và audit split |
| M2 | LSTM một bước | Pipeline train/inference; nạp lại checkpoint đối chiếu dung sai; đo CPU |
| M3 | Khóa thực nghiệm | CNN, multi-step, seeds, tuning, phân tích được định trước test |
| M4 | Validation | Run và audit; chọn cấu hình/seed phục vụ trước khi xem test |
| M5 | Đánh giá cuối | Test, mọi seed, lỗi/giới hạn; metric tính lại được |
| M6 | Phát hành | Bộ dataset/model/scaler/config/results/audit nạp độc lập |
| M7 | Web tích hợp | API/UI một/năm bước, lỗi/release/trace được kiểm tra |
| M8 | Bàn giao | Máy thành viên khác chạy; đủ bảy mục coursework |

Chưa đặt ngày hoặc phân công khi chưa có dữ kiện. Web có thể phát triển song song sau M0 với dữ liệu mẫu gắn nhãn; kết nối validation sau M2. Test không dùng phát triển giao diện/model. Mốc không tự đạt chỉ vì có file; bằng chứng kiểm tra chưa có phải ghi chưa kiểm chứng.
