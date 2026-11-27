# artifacts/scalers

Scaler train theo run/dataset.

TV2 mục 4 đã tạo scaler thật trong `aapl_scaler_20261120T124720810874Z/`: scaler.json và manifest.json, chỉ fit 2014 giá train 2015–2022 từ snapshot TV1 đã chốt. Các file sinh ra không commit Git, không tự upload Drive. Tái tạo bằng `scripts/build_tv2_scaler.py --dataset-version <version>` trong môi trường TV2 đủ dependencies; mỗi lần tạo ID mới.

Khi bàn giao cần chuyển nguyên thư mục scaler cùng bộ snapshot TV1 tương ứng, kiểm tra manifest/checksum và gọi load_scaler với version/hash đã xác minh. Không chỉ chuyển scaler.json. Chưa upload artifact scaler hoặc xác nhận máy thành viên khác trong mục này.
