# TV5 — cài đặt, tái lập và bàn giao

Phạm vi TV5 là CNN một bước và phép so sánh validation với LSTM/persistence. Final test2024–2025, multi-step evaluation, API/release thuộc TV6. Không cần Docker để chạy local theo môi trường đã kiểm chứng.

## Môi trường

Python3.13.7, PyTorch2.14.1+cpu, dependencies ghim tại scripts/requirements-tv4-lock.txt. Dùng venv sạch không system/user site. Máy hiện tại dùng .venv/tv4_clean. Ví dụ PowerShell trên máy nhận, sau giải nén vào thư mục làm việc riêng

```powershell
py -3.13 -m venv .venv/tv5
.venv/tv5/Scripts/python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1+cpu
.venv/tv5/Scripts/python.exe -m pip install -r scripts/requirements-tv4-lock.txt
.venv/tv5/Scripts/python.exe scripts/verify_tv5_handoff.py
```

Đây là hướng dẫn setup, không tuyên bố đã cài lại dependency qua mạng hoặc xác nhận máy thành viên khác. Verifier kiểm version lock, nguồn import, payload hashes, tests, forward dữ liệu, nạp sáu model và tái tính metric/monitoring. Các kiểm tra dùng venv sạch có sẵn nhưng source đã tách ở thư mục riêng. Không train lại trong verifier.

## Gói local và nguồn Git

ZIP TV5 có source/docs/tests/notebooks, dependencies TV1/TV2 raw/validated/scaler/prepared và bằng chứng local TV4 cần cho notebook/so sánh. Có ba best CNN research checkpoints, ba LSTM lookback30 comparison checkpoints và best smoke diagnostic; không gom các checkpoint intermediate dư thừa. Chưa có quyền phân phối dữ liệu rộng được xác minh, gói local chỉ bàn giao coursework theo phạm vi được phép. Không upload hoặc commit data/weights/logs/ZIP.

Mỗi payload file có SHA256 trong TV5_HANDOFF.json, ZIP có sidecar .zip.sha256. Không giải nén đè workspace đang làm. Khôi phục đúng relative paths, tránh dựa vào đường dẫn tuyệt đối trong logs lịch sử. Pointer logs/audit/tv5_item10_latest.json ngoài gói chỉ vị trí ZIP và receipt mới nhất, không tự là bằng chứng người nhận đã chạy.

## Lệnh thực nghiệm và notebook

```powershell
python scripts/check_tv5_aapl_data.py
python scripts/run_tv5_smoke.py
python scripts/run_tv5_official.py
python scripts/compare_tv5_validation.py
python scripts/build_tv5_monitoring.py
python scripts/build_member_notebooks.py --member 5 --overwrite
python scripts/execute_member_notebooks.py --member 5
```

Dùng Python venv ở trên thay `python` khi máy có nhiều Python. Build notebook có --overwrite xóa output cũ, cần execute ngay sau đó. Notebook05 dùng kernel aapl-coursework-tv5 và thư mục notebooks. Executor đặt Jupyter local path, có thể cần quyền kernel/socket trên Windows.

Smoke tạo run mới5 epoch seed42 purpose diagnostic. Official entry point kiểm cnn_one_step_option_a.lock.json, ba seed42/123/456, max100/patience10/trần300, không đổi tuning vì bảng validation. Lệnh train thực sự chạy lại và sinh artifacts mới; để xem kết quả có sẵn chỉ mở notebook hoặc chạy comparison/monitoring.

## Nạp CNN cho consumer

Dùng backend.artifacts.cnn_checkpoint.load_cnn_checkpoint với expected_provenance gồm sáu trường PROVENANCE, expected_model_config, expected_training_config_sha256 và expected_run_id/expected_seed. Các expected values lấy từ official.yaml, accepted data provenance và run receipt đáng tin cậy. Không tự tin manifest chỉ vì manifest tự khai hash. Default từ chối diagnostic; chỉ truyền allow_diagnostic=True khi kiểm diagnostic. Artifact chứa best weights/inference state, không có Adam/RNG state để resume.

## Giới hạn

Validation được dùng chọn checkpoint/lookback, chưa là holdout test. Persistence tốt hơn cả sáu model trên validation2023, không ép model phải thắng baseline. LSTM tìm lookback10/30/60 còn CNN một kiến trúc nên ngân sách khác nhau. Không xác nhận lợi nhuận, độ trễ production hoặc không overfit chỉ từ bảng metric.

Chưa có peak RAM lịch sử, live TensorBoard CNN/production drift/alerting. Chưa xác nhận máy người nhận hoặc API. Verifier chỉ kiểm tái lập artifact/forward/metrics bằng nguồn tách riêng trên máy local, không tuyên bố đã lặp lại toàn bộ training từ đầu hoặc trên OS khác.
