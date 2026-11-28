# Tái lập và phát hành

Mục10 có `scripts/build_tv6_web_handoff.py` tạo ZIP runtime web local mới gồm API/frontend/sidecar và release artifacts đúng đường dẫn. Checksum/receipt ở `logs/audit/tv6_web_handoff_latest.json`. Giải nén riêng rồi chạy `scripts/verify_tv6_web_handoff.py --http` bằng môi trường người nhận. Không thay ZIP inference v1, không tự upload; full research RunAll/training cần artifacts/logs nghiên cứu ngoài gói runtime. Máy khác và quyền phân phối dữ liệu chưa được xác nhận.

Run: ID duy nhất, cấu hình, seed, Git commit/trạng thái chưa commit, môi trường, dataset hash, scaler, checkpoint, logs, predictions, metric và audit. Không ghi đè run cũ.
Release: liên kết các run/model phù hợp một/năm bước, dataset, scaler/config và kết quả. Chọn seed phục vụ trước test, không chọn test đẹp nhất.
Web dùng release cụ thể, không train lại. Dùng artifacts/checkpoints cho run và artifacts/releases cho bộ phát hành. Cách sao chép hoặc tham chiếu trọng số chốt khi triển khai; không nhân đôi tùy tiện.
Kiểm tra nạp lại dự báo, metric tính lại, cùng môi trường và máy thành viên khác. Seed không bảo đảm đồng nhất tuyệt đối mọi máy.
Git lưu source/docs/config; dữ liệu/checkpoint/output không tự commit. Khi bàn giao release cần hướng dẫn nhận đủ artifacts, không chỉ clone code. Kênh phân phối hiện tại là thư mục Drive được ghi bên dưới.

## Kênh bàn giao artifacts — cập nhật 19/11/2026

Theo yêu cầu người dùng, dùng [thư mục Drive Project_CW](https://drive.google.com/drive/folders/16HyJmtmQ0YzfGHAGGtQ_qTSNEc6lQMwl) cho các lần upload tiếp theo. Đã upload gói raw snapshot TV1 và checksum; chi tiết tại `reports/audits/TV1_Snapshot_Handoff.md`. Đây chưa phải release model hoặc bàn giao validated đầy đủ. Luôn kiểm tra kết quả upload, thư mục cha và giữ hash; không thay đổi quyền chia sẻ khi chưa được yêu cầu.
