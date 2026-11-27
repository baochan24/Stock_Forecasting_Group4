# TV3 — kết quả bàn giao kỹ thuật local

Ngày23/11/2026. **Source/model/trace/adapter và tài liệu TV3 đã sẵn sàng kỹ thuật local cho TV4/TV6.** Chưa có xác nhận người nhận/máy khác, chưa có checkpoint AAPL huấn luyện chính thức; không tuyên bố toàn project đã dự báo hiệu quả.

## Gói cuối

- ZIP `artifacts/releases/TV3_Handoff_20261123T032109345167Z.zip`,669392 bytes.
- SHA256 `bf121e8f1f07ef2860f35b67471260abb5037ad8e4be7bf03683899958964307`; checksum riêng cùng tên thêm `.sha256`.
- Receipt `logs/audit/tv3_package_20261123T032109345167Z/summary.json`.
- Gồm98 file có hash và1 notebook bảo vệ theo hash cell sources. Source/tests/lock68/docs cốt lõi/đề gốc, model1/5/trace/TV2 adapter, checkpoint persistence helper và artifacts TV1/TV2 cần thiết. Không .git/.venv/secrets hoặc weights AAPL đã train.
- HANDOFF_TV3.json ghi model configs/float64/source hashes/Git head/dirty; source có thay đổi chưa commit, Git head không đại diện toàn bộ code. `trained_checkpoints=[]`, `recipient_machine_verified=false`, `checkpoint_training_verified=false`.

Bản chuẩn bị trước TV3_Handoff_20261123T031923212863Z được giữ nguyên theo chính sách bất biến; bản cuối trên bổ sung đầy đủ tài liệu core/đề gốc và là gói dùng bàn giao. Không ghi đè run cũ. ZIP được tạo trước báo cáo cuối này; kết quả hậu kiểm cung cấp riêng ở workspace. Notebook trong gói có source mục6, outputs có thể cần Run All sau verify; outputs mới được phép thay đổi vì manifest bảo vệ cell source, không khóa output.

## Kết quả kiểm chứng

1. `scripts/run_tv3_checks.py --require-clean`: **99/99 đạt**,0 fail/error/skip, venv sạch CPU/float64/lock68 khớp. Evidence `logs/audit/tv3_tests_20261123T031653515947Z/summary.json`.10 cases mới kiểm diagnostic rejection mặc định, state_dict exact roundtrip, wrong data/scaler/horizon/lookback, hash corruption và float32-state silent cast, ID trùng, nhãn trained=True thiếu selection metadata. Tất cả dùng model/file tạm tổng hợp.
2. Giải nén ZIP cuối vào `.venv/tv3_handoff_verify_20261123T032109345167Z`, chạy `scripts/verify_tv3_handoff.py` từ source gói bằng tv3_clean: tests99/99, integration5460 mẫu và trace6 stages đều exit0; protected hashes và notebook source hashes khớp trước/sau. Không training/metric AAPL.
3. Receipt/bản sao summaries ở `logs/audit/tv3_handoff_repro_20261123T032140745602Z/`: verify_summary.json, tests_summary.json, integration_summary.json, trace_summary.json. Logs đầy đủ tại thư mục giải nén/logs/audit/tv3_handoff_verify_20261123T032140745602Z.
4. Notebook03 cập nhật mục6, kiểm checksum ZIP/manifest/receipt và hiển thị configs, số checkpoint train bằng0, người nhận false. **22 cells/13 code,13/13 code đạt**, không error outputs; evidence `logs/audit/member_notebooks_20261123T032341382654Z/summary.json`. Bảng tests99 cases và output từng mục đã lưu, không cần Run All chỉ để xem.

## TV4 và TV6 sử dụng như thế nào?

Theo docs/TV3_Handoff_TV4_TV6.md. TV4 nhận LSTMOneStep/LSTMMultiStep và batch CPU float64 để xây loop/validation/early stopping; train và checkpoint riêng1/5. Module artifacts/lstm_checkpoint.py không quyết định lúc train/lúc save. TV4 chọn best validation checkpoint, cung cấp run_id/dataset_version/5 source hashes/scaler_id/trained/selected_on/best_epoch và logs/config/seed thực tế.

TV6 nhận loader kiểm class/horizon/lookback/float64/source/scaler/hash trước strict load, trả eval CPU model; default từ chối diagnostic trained=False. Chỉ allow_diagnostic=True cho unit/demo kỹ thuật. Weights_only=True và checksum không thay thế nguồn tin cậy hoặc bằng chứng train. Metadata do caller ghi, không tự chứng minh training history. Inference chỉ X, inverse dùng scaler đúng bộ; trace1 sample/schema nội bộ chờ TV6 duyệt API, không suy ý nghĩa kinh tế từ gate.

## Còn chờ để nghiệm thu phối hợp

- Thành viên khác tự setup/verify gói và gửi thông tin người/máy/OS/Python/ZIP SHA/lock hash/logs.
- TV4 thực hiện training/validation/official checkpoint; TV3 hỗ trợ kiểm reload/trace checkpoint đó khi có.
- TV6 thống nhất schema trace/API và test consumer release/inference/evaluation.

Không tự gửi tin cho thành viên khác, upload Drive, push/merge hoặc train thay TV4 trong mục này. Nghiệm thu kỹ thuật local TV3 không có nghĩa TV4/TV6 đã nhận hoặc toàn hệ thống đã sẵn sàng dự báo.
