# Tái lập và phát hành

Run: ID duy nhất, cấu hình, seed, Git commit/trạng thái chưa commit, môi trường, dataset hash, scaler, checkpoint, logs, predictions, metric và audit. Không ghi đè run cũ.
Release: liên kết các run/model phù hợp một/năm bước, dataset, scaler/config và kết quả. Chọn seed phục vụ trước test, không chọn test đẹp nhất.
Web dùng release cụ thể, không train lại. Dùng artifacts/checkpoints cho run và artifacts/releases cho bộ phát hành. Cách sao chép hoặc tham chiếu trọng số chốt khi triển khai; không nhân đôi tùy tiện.
Kiểm tra nạp lại dự báo, metric tính lại, cùng môi trường và máy thành viên khác. Seed không bảo đảm đồng nhất tuyệt đối mọi máy.
Git lưu source/docs/config; dữ liệu/checkpoint/output không tự commit. Khi bàn giao release cần hướng dẫn nhận đủ artifacts, không chỉ clone code. Kênh phân phối chưa chốt.
