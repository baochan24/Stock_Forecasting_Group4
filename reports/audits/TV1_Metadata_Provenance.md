# TV1 — hạng mục 3: metadata và nguồn gốc

Snapshot: `aapl_2015_2025_acq_20261119T141302002415Z`. Dùng `inspect_snapshot_provenance` ở `backend/data/validation/provenance.py` để kiểm tra khai báo nguồn và raw hiện có, không sửa dữ liệu/metadata.

Kiểm tra: version, AAPL/USD, Yahoo Finance/yfinance, phiên bản thư viện, phạm vi 2015–2025, UTC timestamp, chính sách Adj Close/auto_adjust=False, giới hạn hồi cứu, đường dẫn raw, SHA-256, số dòng, schema và ngày đầu/cuối. Notebook hiển thị kết quả từng kiểm tra và lưu `data/metadata/aapl_provenance_report_<dataset_version>.json`.

Validator đã gọi phép kiểm tra này trước khi tạo validated. Báo cáo validation về sau sẽ chứa provenance, raw hash, metadata path/hash, currency và chính sách điều chỉnh để liên kết nguồn với đầu ra. Chưa tạo validated CSV/report, không công bố hoàn tất kiểm định chất lượng hay lịch phiên.

Hash chỉ chứng minh byte nhất quán với khai báo đã lưu; không phải xác thực độc lập Yahoo hoặc chữ ký nguồn. Chính sách dạng văn bản cũ được kiểm tra theo quy ước hiện tại; không tự đổi schema nguồn hoặc rewrite snapshot.

Tests: `python -m unittest discover -s tests/data -p test_provenance.py -v`; dùng fixture tổng hợp được ghi rõ, kiểm tra metadata đúng, trường thiếu/sai, raw bị sửa. Kết quả thực thi và số kiểm tra snapshot được lưu trong notebook sau khi chạy.

Kết quả đã chạy 19/11/2026: snapshot đạt 16/16 kiểm tra, không có lỗi; 4/4 test provenance đạt; test hồi quy bảng hợp lệ của validator cũ cũng đạt. Notebook chạy thành công. Không thay hash raw hoặc metadata nguồn. Các test phụ thuộc artifacts version cũ chưa được coi là đã đạt.

Báo cáo JSON của lần chạy đã upload vào Drive Project_CW: [mở báo cáo provenance](https://drive.google.com/file/d/1_GClIr7JlMuZ5t-J8KzyI8kwIhmonD5t/view?usp=drivesdk). File được upload là kết quả tại thời điểm kiểm tra; chạy lại notebook sẽ tạo timestamp kiểm tra mới ở máy.
