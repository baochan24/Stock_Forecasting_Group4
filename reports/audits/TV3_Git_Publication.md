# TV3 — chuẩn bị công bố source lên Git

Ngày 23/11/2026, theo yêu cầu người dùng: cập nhật nhánh `Thien-code137-patch-1` của `baochan24/Stock_Forecasting_Group4`.

- Bắt đầu từ head remote `1f209b70c5690fb5e41b3b26d8eab36b2b6c029d`, trong checkout riêng `.venv/tv3_publish_20261123`; không thay index/staging của workspace chính hoặc checkout lồng.
- Bao gồm source TV3, tests, notebook có outputs, scripts/lock, tài liệu và các module TV1/TV2 cần cho adapter và kiểm tra provenance. Không merge nhánh TV2 hoặc main.
- Không công bố dataset, scaler, prepared arrays, checkpoints, logs sinh ra, ZIP, venv hoặc secrets. Các artifacts cần nhận theo TV3 Final Handoff.
- Kiểm chứng chính bản source chuẩn bị push: `scripts/run_tv3_checks.py --require-clean`, **99/99 tests**, 0 fail/error/skip, môi trường CPU sạch; evidence local `.venv/tv3_publish_20261123/logs/audit/tv3_tests_20261123T033713746451Z/summary.json`.
- Model mặc định CPU float64; import từ `backend.models.lstm_one_step`, `backend.models.lstm_multi_step` và `backend.model_trace`. Giữ nguyên các thư mục upload cũ tại gốc như lịch sử, không dùng chúng làm source hiện hành.
- Không có checkpoint AAPL huấn luyện chính thức; chưa xác nhận máy người nhận. Unit tests không cần dữ liệu thật; integration và Run All notebook cần artifacts cùng các receipt được hướng dẫn trong tài liệu bàn giao.

Tài liệu này ghi phạm vi và bằng chứng chuẩn bị. SHA và trạng thái push phải đối chiếu commit/remote thực tế sau khi công bố; không suy từ file này rằng push đã thành công.
