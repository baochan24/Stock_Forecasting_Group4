# Khắc phục audit TV4 mục 1–9

Ngày 26/11/2026. Xử lý các vấn đề trong TV4_Items1_9_Review_20261126.md trước khi chuyển sang mục 10.

## Giao diện checkpoint

Đã loại helper import save_checkpoint chưa tồn tại. Khi caller truyền checkpoint_dir, trainer yêu cầu checkpoint_saver callable và kiểm trước khi cập nhật model hoặc tạo thư mục. Callback chịu trách nhiệm lưu và trả đường dẫn checkpoint. Consumer dùng run_experiments để có callback lưu LSTM và provenance đầy đủ. Chế độ checkpoint_dir=None, không callback vẫn chọn best trong RAM.

Đã cập nhật các tests mock về giao diện callback và thêm regression tests xác nhận lời gọi thiếu callback dừng trước khi thay weights hoặc tạo thư mục, callback hợp lệ lưu thật và nạp lại khớp. Strict TV4 đạt 69/69, không skip, môi trường sạch. Phép thử AAPL 33 cửa sổ train/validation bằng runner với callback thật vẫn lưu/nạp thành công. [Receipt tests cuối](../../logs/audit/tv4_tests_20261126T023618816111Z/summary.json) · [Receipt phép thử thật](../../logs/audit/tv4_item5_20261126T023227186038Z/summary.json)

## Trạng thái tài liệu

Open Decisions đã tách các quyết định TV4 đã chốt khỏi phần CNN còn mở. known_pending trong runner tests chỉ còn việc nghiệm thu độc lập/consumer của mục 10. Progress có bảng trạng thái hiện tại 1–9 và giữ lịch sử ở phần thu gọn. Hai notebook cập nhật thông báo đã sửa các vấn đề audit.

## Source lịch sử và tính di chuyển

Đã đối chiếu hash backend của cả 12 run rồi lưu bản source bất biến trước sửa vào logs/audit/tv4_pre_fix_source_20261126/backend. Entry point mục 8 được khôi phục chính xác và kiểm SHA256 bằng hash đã lưu lúc chạy, entrypoint mục 9 cũng được lưu riêng. Các phiên bản này mô tả đúng code đã dùng, khác phiên bản sửa giao diện hiện tại.

Manifest TV4_Run_Assets.json liệt kê đường dẫn tương đối, checksum và mapping 12 checkpoint/metadata. verify_tv4_assets.py nhận --root để nạp từ root mới, giữ nguyên log và manifest checkpoint gốc. CLI train nhận --plan-dir để dùng cấu hình bàn giao ở vị trí chỉ định.

Đã sao chép bộ inventory sang thư mục .venv/tv4_relocated_20261126T023348742702Z và chạy kiểm trên root khác. Checksum 323 file và nạp mới 12 model đều đạt, MSE validation khớp meta với rtol 1e-12. Đây là kiểm chứng di chuyển trên cùng máy. Xác nhận máy người nhận và phát hành gói thuộc mục 10.

## Giới hạn giữ nguyên trong báo cáo

Các run best ở epoch 100 vẫn là kết quả theo ngân sách đã chốt. Chưa có cơ sở tuyên bố hội tụ hoàn toàn. Không thay đổi hay train lại các checkpoint chính thức trong lần sửa này. Đánh giá test và so sánh baseline/CNN thuộc giai đoạn sau.

Các sai sót audit về giao diện, trạng thái và đường dẫn đã có phương án thực thi được kiểm chứng. Bước kế tiếp là mục 10 theo flow.
