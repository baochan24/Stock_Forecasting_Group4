# audit

Kiểm tra quy tắc xuyên giai đoạn; ghi đạt/không đạt và bằng chứng. Không âm thầm sửa dữ liệu.

Trạng thái: vị trí triển khai dự kiến; chưa có code hoặc kiểm chứng. Chưa chọn tên file implementation để tránh tạo stub chạy giả.

TV2 mục 9: `tv2_leakage.py` có audit_train_statistics và audit_temporal_windows, tính oracle độc lập theo ngày nguồn/train numpy moments, đối chiếu coverage/exclusions/contract và lưu ví dụ đối chiếu khi CLI điều phối. Không sửa nguồn hoặc điều khiển training. CLI `scripts/audit_tv2_leakage.py` còn kiểm tra perturbations trong bản sao bộ nhớ, input-only adapter và hashes không đổi. Đây là audit preprocessing local, chưa chứng nhận model/training/test-tuning.
