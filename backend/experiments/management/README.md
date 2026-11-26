# experiments/management

Run ID, seed, môi trường, logs và trạng thái. Không kiêm quyết định model thắng.

TV4 mục1: experiment_manager.py nhận từ PR#10, quản lý seed/run_id, tạo thư mục, lưu CSV/config và metadata. Runner ở backend/experiments/runner, không có bản trùng trong management.

Khi runner sử dụng bộ dữ liệu AAPL ở mục 3, hàm ghi metadata nhận năm hash nguồn TV1, ID scaler/prepared và hash manifest từ dataset đã xác minh. Mục 4 nghiệm thu lịch sử training/validation và cách ghi log khi run lỗi.

Runner ghi cấu hình, tạo lịch sử CSV và metadata trạng thái `running` trước khi tạo model. Sau mỗi epoch hoàn tất train và validation, runner thay CSV bằng bản mới. Metadata kết thúc ghi `completed`, `failed` hoặc `interrupted`, seed, hash mã nguồn, số luồng PyTorch, thời điểm bắt đầu/kết thúc và best epoch đã quan sát. Nếu tiến trình bị hệ điều hành chấm dứt cưỡng bức, trạng thái có thể còn `running`; CSV chứa các epoch đã ghi xong.
