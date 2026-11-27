# Audit TV4 mục 1–9 trước nghiệm thu cuối

**Cập nhật sau sửa.** Các vấn đề bên dưới đã được xử lý theo yêu cầu người dùng, xem [báo cáo sửa lỗi và kiểm chứng](TV4_Audit_Fixes_20261126.md). Phần còn lại giữ nguyên kết quả audit trước sửa để truy vết.

Ngày 26/11/2026. Phạm vi audit source hiện tại, cấu hình, bằng chứng dữ liệu, logs, 12 checkpoint và hai notebook. Báo cáo sai sót trước khi triển khai mục 10.

## Kết luận

Các run chính thức và checkpoint được kiểm tra lại đạt. Chưa nên coi toàn bộ giao diện bàn giao đã hoàn chỉnh. Một lỗi ở đường gọi trainer trực tiếp cần sửa, cùng các mục đồng bộ tài liệu và đóng gói tái lập.

## Sai sót và việc cần xử lý

### 1. Đường gọi trainer trực tiếp còn lỗi lưu checkpoint

Mức ảnh hưởng trung bình, có thể chặn consumer gọi trực tiếp. Hàm train_model vẫn nhận checkpoint_dir và mặc định checkpoint_saver=None. Khi validation cải thiện, nhánh này gọi _save_best_checkpoint, import backend.artifacts.save_checkpoint chưa tồn tại. Probe gọi helper tái hiện RuntimeError với thông báo TV6 must implement backend.artifacts.save_checkpoint().

Các run mục 8/9 đi qua run_experiments, truyền callback save_selected dùng save_lstm_checkpoint nên kết quả 12 run đã xác minh vẫn hợp lệ. Cần thống nhất giao diện trainer công khai, loại đường gọi lưu không hoạt động hoặc yêu cầu rõ callback và kiểm tra trước khi train. Cần test qua chính train_model cho trường hợp consumer này.

### 2. Tài liệu và receipt còn trạng thái cũ

Mức ảnh hưởng thấp về thực thi, đáng kể khi đọc nghiệm thu. scripts/run_tv4_checks.py vẫn ghi known_pending là real checkpoint hook and reload item5, dù đã hoàn thành. docs/10_Open_Decisions.md còn ghi seeds/lookback và quy ước độ lệch chuẩn là mở trong khi mục 7 đã chốt. TV4_Progress giữ nhiều đoạn chờ từ lịch sử, bảng flow cũng còn các trạng thái cũ. Cần có một bảng trạng thái hiện tại rõ ràng và đánh dấu phần lịch sử.

### 3. Phụ thuộc đường dẫn máy và source chưa đóng gói cho tái lập

Đây là phần còn phải hoàn thiện ở mục 10. Cấu hình chính thức nằm trong logs/audit và tham chiếu ID prepared mới; log/checkpoint dùng nhiều đường dẫn tuyệt đối Windows. Các CLI train và notebook ghim timestamp của workspace. Máy clone cần bộ artifacts tương ứng và hướng dẫn ánh xạ, chỉ source Git chưa đủ để chạy lại đúng kết quả.

Script entrypoint mục 8 được mở rộng thêm --five-step cho mục 9 nên hash file hiện tại khác bản chạy mục 8. Hash cũ vẫn được lưu, nhưng chưa có bản source bất biến đi cùng đợt train để đối chiếu độc lập đầy đủ. Cần manifest và bản source/config tương ứng trong công việc tái lập. Điều này chưa chứng minh thay đổi logic train hay mất tính đúng đắn của weights.

## Đối chiếu từng hạng mục

| Mục | Kết quả audit | Điều còn lưu ý |
|---|---|---|
| 1 | Imports workspace và môi trường strict đạt | Tiếp nhận lịch sử có receipt riêng |
| 2 | CPU float64 và guards được kiểm bằng bộ tests | Không thay dtype |
| 3 | Payload prepared có checksum, input/target đúng shape | Bàn giao đủ artifacts theo YAML |
| 4 | Log, finite losses, best epoch khớp minimum | Đường gọi trực tiếp lưu checkpoint cần sửa |
| 5 | Nạp mới 12 checkpoint và đo MSE đạt | Giao diện helper cũ còn tồn tại |
| 6 | Có smoke/timing và conditions CPU | Timing phụ thuộc máy/tải nền |
| 7 | Lưới 12 run và common dates đã xác minh | Đồng bộ Open Decisions và config bàn giao |
| 8 | Chín run, 775 epoch, chọn lookback 30 đúng quy tắc | Bốn run chạm 100, hai best ở 100 |
| 9 | Ba run, 300 epoch, MSE tổng/từng horizon khớp | Cả ba best ở 100, chưa chứng minh hội tụ |

## Kiểm chứng thực thi mới

Strict TV4 đạt 67/67 tests, không skip, môi trường sạch, imports đúng workspace. [Receipt tests](../../logs/audit/tv4_tests_20261126T022544598775Z/summary.json)

Đọc và đối chiếu checksum mọi payload prepared liên quan. Nạp 12 checkpoint vào instance mới, chạy trên các mảng validation tương ứng, gồm lọc common60 cho một bước. MSE tổng và từng horizon khớp best log với rtol 1e-12. Kiểm best_epoch, trạng thái completed, finite losses/thời gian và validation notebook. Hai notebook đều đủ 37 cell, các code cell đã chạy và không có error output. [Receipt kiểm tra 12 model](../../logs/audit/tv4_items1_9_20261126T022627037333Z/summary.json)

## Giới hạn nghiên cứu

Tổng 1.075 epoch nằm trong ngân sách 1.200 đã chốt. Các run chạm cap cần ghi giới hạn, không tự tăng ngân sách sau khi xem kết quả. Chọn lookback bằng validation là đúng kế hoạch. Đánh giá test, MAE/RMSE USD và so sánh persistence/CNN thuộc các bước đánh giá sau. Adjusted close có chính sách điều chỉnh hồi cứu, cần giữ giới hạn point-in-time trong báo cáo dữ liệu.

Ưu tiên trước khi chốt bàn giao là sửa giao diện lưu trainer và đồng bộ tài liệu. Mục 10 tiếp theo chịu manifest, source/artifacts/config tái lập và xác nhận consumer.
