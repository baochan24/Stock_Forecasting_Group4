# Dữ liệu: nguồn, quyền sử dụng và giới hạn

Kiểm tra tài liệu nguồn ngày28/11/2026. Snapshot project lấy Yahoo Finance qua yfinance, dùng cho coursework AAPL. Điều này ghi nhận nguồn và mục đích của nhóm, không tự chứng minh quyền tái phân phối dataset.

[README chính thức của yfinance](https://github.com/ranaroussi/yfinance#readme) nêu thư viện không liên kết/được Yahoo bảo chứng, hướng đến nghiên cứu/giáo dục và yêu cầu người dùng tự xem điều khoản đối với dữ liệu tải về. Giấy phép mã nguồn thư viện không đồng nghĩa giấy phép cho dữ liệu Yahoo.

Nguồn điều khoản cần đối chiếu: [Yahoo Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html), [Yahoo Finance data providers](https://help.yahoo.com/kb/SLN2310.html). Trong lượt kiểm hiện tại hai trang trực tiếp trả lỗi999/429, nên không tuyên bố đã xác minh đầy đủ điều khoản hiện hành từ các trang đó. Không dùng trích dẫn tìm kiếm làm căn cứ kết luận đã được cấp quyền.

Project chưa có văn bản cấp quyền phân phối công khai snapshot hoặc xác nhận phạm vi áp dụng từ đơn vị sở hữu dữ liệu. Trạng thái này phải ghi còn mở trong checklist nộp bài; ZIP local/hướng dẫn không thay bằng chứng quyền sử dụng. Không tự upload hoặc cấp quyền chia sẻ mới trong audit cuối.

Nếu nguồn tải tạm không hoạt động, snapshot/hash cố định giúp tái lập thực nghiệm đã có. Nếu không được dùng/phân phối snapshot, cần giảng viên/nhóm chốt nguồn thay thế có quyền phù hợp và tạo phiên bản dữ liệu/thực nghiệm mới; không thay giá dưới dataset_version cũ. Đây là phương án dự phòng, chưa được triển khai hoặc cấp phép.

Về phương pháp, adjusted close được điều chỉnh hồi cứu tại thời điểm tải, không phải dữ liệu point-in-time. Không mô tả demo như dự báo được công bố tại thời điểm lịch sử, không dùng kết quả để khẳng định lợi nhuận giao dịch. Một nguồn dữ liệu, một cổ phiếu và một feature cũng giới hạn khả năng khái quát.
