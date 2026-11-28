# Chi tiết còn mở

- API đã chọn FastAPI/Uvicorn và ghim dependencies ở mục8; frontend mục9 dùng HTML/CSS/ES modules không dependency, proxy localhost. Hình thức triển khai cuối còn mở.
- Đã ghi rõ snapshot Yahoo/yfinance với auto_adjust=False và Adj Close làm adjusted_close; version/hash/giới hạn hồi cứu trong reports02. Quyền phân phối dữ liệu hoặc nguồn thay thế được chấp thuận còn chờ, xem TV6_Data_Use_and_Limits.md.
- Đo thời gian/peak RAM CNN sau tích hợp. TV5 đã chốt phương án A, một kiến trúc hiện có và ba run, tối đa 300 epoch. Từ mục 2 dùng CPU float64, xem Decision Log.
- TV6 mục2 đã khóa numeric tie atol1e-12USD, rolling error20 phiên và top10 errors/run; chưa có practical-significance threshold hoặc phép kiểm ý nghĩa thống kê được chốt. Không dùng numeric tie làm tương đương thực tiễn.
- Schema API, giới hạn/phân trang và trace summary/full đã triển khai mục8; xem TV6_API_Setup_and_Contract.md. Loadtest và deployment cuối chưa nghiệm thu.
- Cơ chế truy vết LSTM được đối chiếu; lịch công việc và phân công.
- Có gói runtime web/checksum local và hướng dẫn nhận artifacts. Chưa tự upload bản mới; xác nhận máy thành viên khác theo TV6_Member_Acceptance.md còn chờ biên bản thật.
Các mục này không được tự coi là đã triển khai hoặc chứng minh.

TV4 đã chốt seeds 42/123/456, lookback một bước 10/30/60, năm bước 30, tối đa 100 epoch, patience 10 và std mẫu ddof=1. Chọn bằng validation MSE trung bình ba seed, hòa chính xác ưu tiên lookback ngắn hơn. Kết quả và giới hạn được ghi trong báo cáo mục 8/9.
