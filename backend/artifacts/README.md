# artifacts

TV5 mục 6 thêm cnn_checkpoint.py. Save/load CNN CPU float64 với config, checksum, provenance dataset/scaler/prepared, run/seed, source hashes và fingerprint training config. Loader yêu cầu expected_provenance đủ sáu trường PROVENANCE, expected_model_config và expected_training_config_sha256 từ cấu hình/handoff đã tin cậy; có expected_run_id/expected_seed tùy chọn. Mặc định từ chối purpose diagnostic hoặc trained=False, muốn kiểm diagnostic phải truyền allow_diagnostic=True. Không ghi đè checkpoint ID. Đây là best-model/inference artifact, không lưu optimizer state để resume. Chi tiết reports/audits/TV5_Item6_Checkpoint_Provenance.md.

TV3 mục6: `lstm_checkpoint.py` save/load state_dict CPU float64 kèm model config/identity/hash/scaler/run metadata, không quyết định training/checkpoint selection. Loader default từ chối trained=False, chặn actual state32 dù manifest ghi64; TV4 chịu tính trung thực best validation epoch/logs, TV6 dùng loader với đúng expected identity/horizon. Chưa có trained checkpoint thật. Hướng dẫn docs/TV3_Handoff_TV4_TV6.md, tests99/99 với temporary diagnostic files.

TV2 mục 10: `prepared.py` lưu/nạp modes1/5 bằng NPZ allow_pickle=False và JSON input/target riêng, identity/source hashes/scaler ID/checksums trong manifest; tạo ID mới, không ghi đè. Loader container không thay thế audit contract/coverage. Verify tại scripts/verify_tv2_handoff.py, hướng dẫn docs/TV2_Setup_and_Handoff.md.

Lưu/nạp và kiểm tra liên kết dataset, scaler, cấu hình, checkpoint, kết quả/release. Không gọi ngược training.

Trạng thái: vị trí triển khai dự kiến; chưa có code hoặc kiểm chứng. Chưa chọn tên file implementation để tránh tạo stub chạy giả.

TV2 mục 4: `scaler.py` thực hiện save_scaler/load_scaler bằng JSON kèm manifest/checksum và snapshot identity. Module chỉ lưu/nạp/kiểm tra; lựa chọn train và fit nằm tại `backend/data/preparation/train_scaler.py`. Không xử lý training/checkpoint/release ngoài scaler. Xem README preparation cho interface và phạm vi kiểm chứng.
