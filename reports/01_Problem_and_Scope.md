# Vấn đề và phạm vi

Đề Topic4 yêu cầu regression từ Yahoo Finance: dùng chuỗi quá khứ để dự báo giá phiên tiếp theo bằng LSTM; mở rộng multi-step và CNN vs.LSTM. Nhóm cụ thể hóa thành AAPL adjusted close2015–2025,30 phiên,CPUfloat64,H1/H5 và persistence. Các thông số này là lựa chọn nhóm, không phải yêu cầu nguyên văn của đề.

Người dùng chính: giảng viên và nhóm nghiên cứu/người học. Mục tiêu là xây dựng pipeline tái lập, mô hình dự báo có kiểm định và demo giải thích được; không đặt điều kiện LSTM bắt buộc thắng baseline.

Input `(B,30,1)` gồm giá đã quan sát. Output `(B,1)` hoặc `(B,5)`, decode USD, có origin/target date/method/seed/run/release. Actual/error ghép sau inference. Web phục vụ model đã train, không training endpoint hoặc dữ liệu live.

Sản phẩm gồm snapshot/provenance,preprocessing,3 kiến trúc và persistence,checkpoint/scaler/config,metric/error analysis,API/frontend,notebooks và hướng dẫn. Kết quả kỹ thuật đạt local; xác nhận máy khác,quyền phân phối dữ liệu và thủ tục nộp cuối còn mở. Xem [ma trận đầu ra](../docs/TV6_Coursework_Output_and_Defense.md).
