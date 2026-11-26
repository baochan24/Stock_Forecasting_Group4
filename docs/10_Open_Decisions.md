# Chi tiết còn mở

- Framework front-end/API và hình thức triển khai, dependencies được xác minh.
- Tham số tải/điều chỉnh giá chính xác sau đối chiếu nguồn và dữ liệu thực.
- Đo thời gian/peak RAM CNN sau tích hợp. TV5 đã chốt phương án A, một kiến trúc hiện có và ba run, tối đa 300 epoch. Từ mục 2 dùng CPU float64, xem Decision Log.
- Dung sai hòa/thua cho đánh giá baseline và số ví dụ phân tích lỗi.
- Schema API chi tiết, phân trang/giới hạn và mức trace.
- Cơ chế truy vết LSTM được đối chiếu; lịch công việc và phân công.
- Kênh phân phối release và kết quả.
Các mục này không được tự coi là đã triển khai hoặc chứng minh.

TV4 đã chốt seeds 42/123/456, lookback một bước 10/30/60, năm bước 30, tối đa 100 epoch, patience 10 và std mẫu ddof=1. Chọn bằng validation MSE trung bình ba seed, hòa chính xác ưu tiên lookback ngắn hơn. Kết quả và giới hạn được ghi trong báo cáo mục 8/9.
