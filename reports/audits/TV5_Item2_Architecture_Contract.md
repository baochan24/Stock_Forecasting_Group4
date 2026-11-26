# TV5 mục 2 — kiến trúc và contract

Ngày 26/11/2026. Phương án A giữ nguyên CNN 17.057 tham số, Conv 1→16→32 kernel3/padding1, MaxPool2, Dropout0,1, Linear480→32→1. Lookback 30, một feature và output một phiên.

## Precision và ranh giới

Agent chọn CPU float64 khi thực hiện yêu cầu hoàn thành mục 2 để đồng nhất với TV2/LSTM. Các layer khởi tạo dtype64 trực tiếp, global dtype không đổi. Forward không cast input. Kiểm config số dương/kiểu hợp lệ, một bước, dropout hữu hạn; từ chối input sai dtype/device/shape, batch rỗng, NaN/Inf và output không hữu hạn.

Đây là lựa chọn thiết kế cho phép so sánh cùng precision, chưa là bằng chứng model tốt hơn. Ngân sách vẫn ba seed 42/123/456, Adam0,001, batch32, max100/patience10 và trần 300 epoch. Không mở thêm cấu hình CNN.

## Kiểm chứng

Hai file test CNN có tổng 26 tests đạt, không skip. Bảy tests ban đầu được cập nhật input theo contract float64. Các tests mới kiểm config/horizon sai, dtype, batch B1, số tham số, global dtype và NaN/Inf. [Receipt tests](../../logs/audit/tv5_tests_20261126T033107306495Z/summary.json)

Notebook 05 chạy 4/4 code cell. Giữ receipt baseline 7 tests float32 ở mục 1, trình bày contract hiện tại và các thay đổi source có chủ đích. Các module/notebook TV1–TV4 được đối chiếu với hash bảo vệ và giữ nguyên. [Biên bản notebook](../../logs/audit/member_notebooks_20261126T033053953695Z/summary.json)

Source trước sửa được lưu tại logs/audit/tv5_item2_source_before, receipt tiếp nhận ban đầu vẫn bất biến. CNN chưa nối artifacts AAPL, factory/runner hoặc checkpoint trong mục này. Tiếp theo là mục 3, kết nối dữ liệu TV2 theo cùng mẫu/ngày/scaler với LSTM.

Audit bảo vệ TV4 ghi nhận README CNN thay đổi so với intake TV4 cũ. Hash tài liệu thay đổi có chủ đích được lưu riêng trong TV5_Item2_Source_Changes.json và được runner đối chiếu cùng receipt TV4 cũ. Các kiểm tra hash còn lại được giữ đầy đủ.

Lượt hồi quy TV4 cuối đạt 69/69 tests, audit passed, môi trường sạch và không có thay đổi bảo vệ ngoài danh sách đã ghi nhận. [Receipt hồi quy](../../logs/audit/tv4_tests_20261126T033324623148Z/summary.json)
