# TV6 mục1 — nghiệm thu đầu vào TV1–TV5

Ngày26/11/2026. Làm tại workspace hiện tại, không lấy trạng thái từ checkout lồng. Scope intake/provenance/history/shape và input-only reload probes, chưa làm protocol final evaluation, API/frontend hoặc inference test.

## Đầu vào

Snapshot aapl_2015_2025_acq_20261119T141302002415Z và scaler aapl_scaler_20261120T124720810874Z. Tái dùng acceptance/quality/calendar/hash TV1 và scaler/prepared/window audits TV2 trong factory TV4. Không fit scaler hoặc sửa dữ liệu. Đối chiếu source/config hashes official CNN với workspace hiện tại, lookback LSTM đã chọn30 từ summary TV4.

Danh mục9 model giữ cả seeds42/123/456 của LSTM một bước, LSTM direct năm bước và CNN một bước. Chọn đúng checkpoint theo best_epoch/run receipt, không lấy đường dẫn mới nhất hoặc seed thắng. CNN kiểm research purpose/config fingerprint/expected provenance/run/seed. LSTM kiểm identity/horizon/lookback và đối chiếu checkpoint training_config/run/seed/source hashes với run metadata. Best epoch được kiểm lại từ toàn epoch_logs.csv, loss hữu hạn và chuỗi epoch liên tục.

Tất cả model nạp strict CPU float64, eval, forward hai mẫu input validation, output shape(2,1)/(2,5) hữu hạn. Không dùng y trong probe hoặc tính metric mới.

## Coverage và sự khác nhau có chủ đích

| Chế độ | Train | Validation | Test chỉ kiểm schema |
|---|---:|---:|---:|
| Một bước, common-history60, input30 | 1.954 | 250 | 502 |
| Năm bước direct, input30 | 1.980 | 246 | 498 |

CNN và LSTM một bước dùng cùng data/prepared/scaler và ordered IDs. LSTM năm bước giữ config TV4 đã train, không tự chuyển train sang common-history60. Train population hai chế độ khác nhau, không so trực tiếp train loss giữa chúng. Năm bước chỉ nhận mẫu có toàn bộ5 targets cùng split nên val/test ít hơn4 windows so một bước. Số test windows chỉ là coverage/schema, không có dự đoán/test metrics trong mục1.

## Danh mục và bằng chứng

scripts/audit_tv6_inputs.py tạo thư mục receipt mới, inventory.json có relative paths/SHA256 của source/config/snapshot/scaler/prepared/weights/manifest/run metadata/history và bảng coverage/model. Check hash lần cuối đảm bảo các file theo dõi không đổi trong lúc audit. Pointer logs/audit/tv6_item1_latest.json chỉ receipt mới nhất, bản danh mục có chủ đích tại reports/audits/TV6_Input_Inventory.json.

Notebook06_TV6_Integration_Evaluation_and_Demo.ipynb dùng builder/executor chung với --member6 và kernel riêng aapl-coursework-tv6. Chỉ tạo/cập nhật notebook TV6, không sửa outputs TV1–TV5.

Lượt kiểm thực tế đạt9/9 model và120 files có SHA256, không sửa source/data trong quá trình audit. Snapshot có2.766 dòng. Receipt logs/audit/tv6_item1_20261126T160646012874Z/inventory.json. Cả9 histories khớp best_epoch/config/run/seed và input-only forward đúng shape/finite. Không tính metrics test hoặc train lại. Môi trường Python3.13.7/Torch2.14.1+cpu, venv tv4_clean sạch hiện có, kernel TV6 riêng.

Notebook TV6 có2 cells, code cell1/1 đã chạy và lưu output gồm bảng9 model,6 dòng coverage và trạng thái10 hạng mục. Receipt logs/audit/member_notebooks_20261126T160825620218Z/summary.json. Output notebooks TV1–TV5 được giữ nguyên.

Đây là nghiệm thu local, không xác nhận máy thành viên khác, release chính thức hoặc protocol test. Tiếp theo mục2 khóa protocol và quy tắc chọn model demo trước khi xem test. Frontend giữ concept đã chốt, chờ mục9.
