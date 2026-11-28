# Kiểm tra dự kiến: integration

TV6 có tests inference/release và `test_tv6_web_handoff.py`. Suite bàn giao mới kiểm payload bị sửa/thiếu, manifest/path không hợp lệ và biên bản UTF-8 không ghi đè: 11/11 đạt trong lượt bổ sung mục10. Verifier gói dùng nguồn giải nén và HTTP thật; xác nhận máy khác vẫn cần người nhận thực hiện. Các dòng kế hoạch ban đầu dưới đây giữ để truy vết.

Đối chiếu pipeline–API–UI, release và máy khác.

Chưa có test thực thi hoặc kết quả pass. Viết kiểm tra có ý nghĩa khi triển khai logic tương ứng.
