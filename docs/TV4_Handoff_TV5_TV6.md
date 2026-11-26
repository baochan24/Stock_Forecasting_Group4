# Bàn giao TV4 cho TV5 và TV6

## Đầu ra

TV4 bàn giao training/validation loop CPU float64 cho LSTM, Adam/MSE, early stopping, callback checkpoint, factory dữ liệu đã xác minh, hai mô hình đã train và notebook có output. Có 12 run nghiên cứu, tổng 1.075 epoch. Bộ model được chọn gồm ba LSTM một bước lookback 30 và ba LSTM năm bước lookback 30, giữ đủ seeds 42/123/456.

Lookback một bước được chọn bằng validation MSE trung bình ba seed. MSE một bước 0,003265939 và năm bước 0,007692942 là các kết quả trên thang chuẩn hóa. Các run chạm 100 epoch cần giữ giới hạn hội tụ trong báo cáo.

## Nhận bộ bàn giao

Gói local nằm ở artifacts/releases/TV4_Handoff_<UTC>.zip, kèm file .zip.sha256. Gói chứa source hiện tại, source lịch sử đúng hash, tests, lock, docs, notebook, cấu hình, artifacts dữ liệu/scaler/prepared và checkpoint. TV4_HANDOFF.json liệt kê checksum payload và sáu model được chọn bằng đường dẫn tương đối. Các log lịch sử còn đường dẫn gốc, verifier dùng mapping tương đối để nạp trên root mới.

Giải nén sang thư mục mới. Đối chiếu SHA256 của ZIP với file đi kèm, tạo môi trường Python 3.13 theo scripts/requirements-tv4-lock.txt. Từ root bản giải nén, chạy các lệnh.

~~~powershell
python -X utf8 scripts/verify_tv4_handoff.py
python -X utf8 scripts/run_tv4_checks.py --require-clean
~~~

Verifier kiểm checksum, nạp mới cả 12 checkpoint và đo lại validation MSE. Strict runner ghi log/JUnit/versions vào logs/audit mới. Môi trường lock đã kiểm trên Windows, CPU. Chứng nhận Linux/macOS hoặc máy người nhận cần kết quả chạy tại máy đó.

Để train lại, chạy scripts/train_tv4_one_step.py với --plan-dir trỏ logs/audit/tv4_item7_20261125T120957429763Z. Thêm --five-step cho năm bước. Lệnh tạo run mới, không resume hoặc ghi đè checkpoint cũ.

## Consumer

TV5 nhận loop, contract dữ liệu, chính sách chọn checkpoint và điều kiện so sánh. So CNN với LSTM lookback 30 trên cùng 1.954 mẫu train và 250 validation. Kiến trúc CNN và ngân sách riêng cần được chốt trong phần TV5. Dtype CNN phải được ghi rõ, loop không tự cast.

TV6 nhận sáu model được chọn cùng scaler, source hashes, config/seed/best epoch và logs. Nạp bằng backend.artifacts.lstm_checkpoint.load_lstm_checkpoint, kiểm version/scaler/horizon/lookback trước inference. Model chỉ nhận X. Inverse bằng scaler đã fit train rồi tính MAE/RMSE USD. Multi-step ghép theo origin, horizon và target_date. Đánh giá test sau khóa cấu hình và so persistence/CNN trên cùng mẫu.

## Phạm vi xác nhận

Đã nghiệm thu trên bản sao khác thư mục, cùng máy, dùng môi trường TV4 sạch đã kiểm theo lock. recipient_machine_verified=false đến khi thành viên nhận chạy và lưu receipt. Báo người/máy, OS/Python, SHA ZIP, lock hash, lệnh, log IDs và kết quả thực tế. Việc gửi ZIP hoặc upload chưa được thực hiện trong mục này.
