# TV5 mục 6 — checkpoint CNN và provenance

Ngày 26/11/2026. Giữ CNN một bước, CPU float64 và pipeline TV4. Không train AAPL hoặc đánh giá test trong mục này.

## Artifact và kiểm tra

`backend/artifacts/cnn_checkpoint.py` ghi weights.pt và manifest.json vào thư mục checkpoint ID mới, không ghi đè. Manifest có model_type/format/dtype/device, toàn bộ kiến trúc, checksum weights và training config fingerprint. Metadata có năm source hashes TV1, dataset/scaler/prepared IDs, hai hash manifest scaler/prepared, run/seed, source code/config hashes và trạng thái trained/purpose. Bản đã train phải ghi best_epoch, best_val_loss hữu hạn và selected_on=validation, epoch không vượt max_epochs.

Loader yêu cầu expected provenance gồm sáu trường trong PROVENANCE, expected architecture và training config fingerprint. Đối chiếu run/seed có thể truyền thêm. Chỉ sau khi kiểm manifest/config/hash mới nạp weights_only trên CPU, kiểm actual dtype64/finite và strict state_dict, trả instance mới ở eval. Không dùng chỉ metadata tự khai làm bằng chứng lịch sử train. Hash kiểm phát hiện hỏng dữ liệu, không phải chữ ký xác thực nguồn.

Purpose diagnostic bị từ chối mặc định, kể cả trained=True từ vài bước train tổng hợp hoặc smoke. Initialized diagnostic có trained=False, không được khai validation selection. Chỉ allow_diagnostic=True mới nạp để kiểm chứng. Research yêu cầu trained=True và validation selection hợp lệ.

## Tích hợp

Runner gọi save_cnn_checkpoint cho CNN, giữ saver LSTM hiện tại và trainer nguyên vẹn. Có checkpoint_purpose, mặc định research. Smoke mục 7 sẽ truyền diagnostic. Loader CNN thiếu provenance bị từ chối trước training. Các file trước sửa được giữ ở logs/audit/tv5_item6_source_before, runner hash có chủ đích ở TV5_Item6_Source_Changes.json.

Artifact phục vụ khôi phục best model/inference, chưa lưu Adam/RNG state để resume training. Chưa có checkpoint CNN AAPL nghiên cứu được nghiệm thu. Kiến trúc/ngân sách phương án A vẫn cần khóa trước mục 8, helper lưu fingerprint đầy đủ nhưng không tự cấm mọi cấu hình khác hợp lệ.

## Kiểm chứng

Tests dùng tensors và identities tổng hợp. Có file roundtrip exact, không ghi đè, diagnostic mặc định bị từ chối, mismatch dataset/scaler/prepared/source hashes/config/run/seed, weights checksum sai, actual float32/NaN/thiếu key/sai shape, metadata selection sai. Ca runner train hai epoch tổng hợp lưu best diagnostic và reload instance mới để tính lại validation MSE bằng best_val_loss. Ca research schema chỉ kiểm nhận metadata hợp lệ, không chứng nhận train thực.

## Kết quả thực thi

Bộ CNN/training đạt 138/138 tests, gồm 27 ca checkpoint CNN, không skip. Receipt `logs/audit/tv5_item4_20261126T041640787129Z/summary.json`, JUnit cùng thư mục. Notebook 05 có 15 cells và 9/9 code cell đã chạy, không output lỗi. Receipt thực thi `logs/audit/member_notebooks_20261126T041534551402Z/summary.json`; cell mục 6 lưu receipt riêng trong logs/audit/tv5_item6_*.

Môi trường Python 3.13.7, PyTorch 2.14.1+cpu, venv tv4_clean hiện có. Không đổi dependencies hoặc môi trường TV1. Các tests file dùng thư mục tạm, không đưa weights/logs vào Git. Bước tiếp theo là mục 7, smoke AAPL có giới hạn và purpose diagnostic.
