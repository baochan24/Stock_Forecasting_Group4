# audit

TV6 mục2 thêm tv6_protocol.py để khóa final evaluation trước test inference. Kiểm fingerprint/policy cùng model/data/cohort hashes từ intake, không train hoặc tính metrics. Lệnh scripts/lock_tv6_protocol.py, mô tả docs/TV6_Final_Evaluation_Protocol.md. Validator chung không được dùng để tự thay protocol sau khi xem test.

Kiểm tra quy tắc xuyên giai đoạn; ghi đạt/không đạt và bằng chứng. Không âm thầm sửa dữ liệu.

Trạng thái: vị trí triển khai dự kiến; chưa có code hoặc kiểm chứng. Chưa chọn tên file implementation để tránh tạo stub chạy giả.

TV2 mục 9: `tv2_leakage.py` có audit_train_statistics và audit_temporal_windows, tính oracle độc lập theo ngày nguồn/train numpy moments, đối chiếu coverage/exclusions/contract và lưu ví dụ đối chiếu khi CLI điều phối. Không sửa nguồn hoặc điều khiển training. CLI `scripts/audit_tv2_leakage.py` còn kiểm tra perturbations trong bản sao bộ nhớ, input-only adapter và hashes không đổi. Đây là audit preprocessing local, chưa chứng nhận model/training/test-tuning.
