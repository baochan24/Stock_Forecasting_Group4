# TV2 — đóng gói và tái lập local (22/11/2026)

**Kết luận:** mục 1–9 có bằng chứng local; mục 10 đã hoàn thành source/artifacts/môi trường sạch/hướng dẫn và kiểm tra ZIP giải nén trên máy hiện tại. **Chưa chốt nghiệm thu liên máy:** thành viên khác cần chạy và ghi xác nhận. Không có model/checkpoint/metric, chưa upload Drive hoặc push GitHub.

## Gói cụ thể

- ZIP: `artifacts/releases/TV2_Handoff_20261122T145943242978Z.zip`, 615002 bytes.
- SHA256: `2102c638b44cae2b078e1f67fea60735f3273ccd0bc8455812b4a3e35c3b1baa`; checksum riêng cùng tên thêm `.sha256`.
- Prepared: `data/prepared/tv2_prepared_20261122T145943242978Z/`.
- Scaler: `artifacts/scalers/aapl_scaler_20261120T124720810874Z/`.
- Dataset: `aapl_2015_2025_acq_20261119T141302002415Z`, đủ 5 artifacts TV1 đã xác minh.
- Receipt: `logs/audit/tv2_package_20261122T145943242978Z/summary.json`.

ZIP có source chọn lọc, tests TV2, lock/setup docs, snapshot/scaler/prepared và leakage evidence. HANDOFF.json ghi hash từng file, Git head/dirty: source có thay đổi chưa commit, không dùng Git head đơn lẻ làm nhận dạng. Không có .git/.venv/secrets/frontend/model. Audit trong ZIP là bản tại thời điểm đóng gói (mục 9); báo cáo này và evidence giải nén tạo sau ZIP được cung cấp riêng, không ghi đè artifact đã chốt.

## Consumer output

| Mode | Train | Val | Test | X | y |
|---|---:|---:|---:|---|---|
| 1 bước | 1984 | 250 | 502 | (B,30,1) | (B,1) |
| 5 bước | 1980 | 246 | 498 | (B,30,1) | (B,5) |

Prepared gồm 6 NPZ X/y/target_indices, 12 JSON input/target riêng và manifest identity/hashes/counts/exclusions. NPZ nạp allow_pickle=False. Raw giá USD, X/y float64; tensor float32 model phải kiểm tra riêng. Không truyền y/targets vào inference. Không refit khi nạp/verify.

## Bằng chứng

1. `.venv/tv2_clean`: Python3.13.7, include-system-site-packages=false, user_site_enabled=false. Lock đủ 15 dependencies, freeze khớp, pip check không lỗi. Không sửa TV1/hệ thống.
2. Suite workspace `scripts/run_tv2_checks.py`: **51/51 đạt, 3.804s**, không fail/error/skip. Evidence `logs/audit/tv2_tests_20261122T145854667783Z/summary.json`, unittest.log, freeze và source hashes. Năm tests persistence mới: roundtrip hai modes/contract, corrupt payload, wrong version/hash/scaler, injected member path, chống ghi đè ID.
3. ZIP giải nén sang `.venv/tv2_handoff_verify_20261122T145943242978Z`; source từ gói chạy bằng venv sạch, **51/51 tests đạt**, không import source ngoài gói.
4. Verifier gói giải nén **passed**: kiểm hash file manifest, accept TV1/scaler/prepared, train moments và independent temporal coverage/contracts. **X/y/indices nạp lại bằng nhau tuyệt đối với dựng mới**; input-only adapter khớp X, cấm fit/partial_fit; protected hashes không đổi.
5. Evidence bản giải nén đã copy về `logs/audit/tv2_handoff_repro_20261122T150046833893Z/`: verify_summary.json, tests_summary.json, unittest.log, requirements-freeze.txt. Đây vẫn là máy hiện tại, không phải máy thành viên khác.

## Nhận gói và chốt liên máy

Làm theo `docs/TV2_Setup_and_Handoff.md`: so SHA ZIP, giải nén thư mục mới, tạo venv sạch/cài lock/pip check, chạy run_tv2_checks.py và verify_tv2_handoff.py. Người nhận ghi người/máy/OS/Python, SHA ZIP, IDs và hai logs. Giữ recipient_machine_verified=false đến khi có xác nhận thực, không ghi thay người nhận. Artifacts không commit theo .gitignore; source/docs/tests/config có thể review/commit riêng khi được yêu cầu.

Giới hạn: mới kiểm chứng Windows/Python3.13.7 máy này; checksum nhất quán không phải chữ ký xác thực. Thư mục ghi dở không có manifest hoàn chỉnh không dùng, retry ID mới. Giá adjusted hồi cứu, lịch NASDAQ→XNYS giữ giới hạn TV1; không chứng nhận training/test-tuning hoặc model vượt persistence. Không tự chuyển sang training/upload vì TV2 đã sẵn sàng kỹ thuật.
