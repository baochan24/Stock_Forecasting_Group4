# TV1 — hạng mục 4: bảo vệ phiên bản snapshot

Downloader kiểm tra tên version hợp lệ, từ chối raw hoặc metadata đã tồn tại trước khi gọi mạng, tạo cả hai output bằng chế độ exclusive `x`. File do tiến trình khác tạo giữa bước kiểm tra và mở file cũng không bị ghi đè. Nếu lỗi được bắt, đóng stream và xóa chỉ file do chính lần gọi tạo. File đã có không bị thay đổi. Không cung cấp tùy chọn force/overwrite.

Nếu tiến trình bị kill hoặc máy mất điện có thể còn bộ file dở; lần gọi sau vẫn bị chặn. Đây là bảo vệ ở mức ứng dụng, không phải filesystem bất biến hoặc cơ chế chống sửa thủ công. Đổi dữ liệu phải tạo dataset_version mới.

Kiểm thử dùng fixture tổng hợp và mock mạng: bộ đầy đủ/bộ thiếu một file bị chặn; lần đầu ghi thành công rồi cùng version bị chặn; version mới không đổi version cũ; lỗi mạng dọn file mới và giữ file khác; file xuất hiện đồng thời được giữ nguyên; version sai bị từ chối trước gọi mạng.

Lệnh: `.venv/eda/Scripts/python.exe -m unittest discover -s tests/data -p test_snapshot_versioning.py -v`.

Kết quả chạy 19/11/2026: 5/5 test versioning đạt; 4/4 test provenance đạt. Notebook chạy thành công; lần thử trên snapshot thật bị từ chối trước gọi mạng và hash raw/metadata giữ nguyên.

Notebook thực thi trên version thật `aapl_2015_2025_acq_20261119T141302002415Z`: thử gọi cùng version với mạng mock, xác nhận FileExistsError, không gọi mạng, hash raw và metadata trước/sau không đổi. Bằng chứng JSON tại `data/metadata/aapl_versioning_report_<dataset_version>.json`. Chưa tạo validated CSV trong hạng mục này.
