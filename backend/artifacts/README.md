# artifacts

TV2 mục 10: `prepared.py` lưu/nạp modes1/5 bằng NPZ allow_pickle=False và JSON input/target riêng, identity/source hashes/scaler ID/checksums trong manifest; tạo ID mới, không ghi đè. Loader container không thay thế audit contract/coverage. Verify tại scripts/verify_tv2_handoff.py, hướng dẫn docs/TV2_Setup_and_Handoff.md.

Lưu/nạp và kiểm tra liên kết dataset, scaler, cấu hình, checkpoint, kết quả/release. Không gọi ngược training.

Trạng thái: vị trí triển khai dự kiến; chưa có code hoặc kiểm chứng. Chưa chọn tên file implementation để tránh tạo stub chạy giả.

TV2 mục 4: `scaler.py` thực hiện save_scaler/load_scaler bằng JSON kèm manifest/checksum và snapshot identity. Module chỉ lưu/nạp/kiểm tra; lựa chọn train và fit nằm tại `backend/data/preparation/train_scaler.py`. Không xử lý training/checkpoint/release ngoài scaler. Xem README preparation cho interface và phạm vi kiểm chứng.
