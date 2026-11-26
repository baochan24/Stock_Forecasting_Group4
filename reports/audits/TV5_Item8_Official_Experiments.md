# TV5 mục 8 — thực nghiệm CNN chính thức

Ngày 26/11/2026. Giữ phương án A đã chốt trước smoke, không tuning theo kết quả mục 7. CNN một bước, lookback30, một feature, 17.057 tham số, CPU float64 và một Torch thread. Dữ liệu/scaler/prepared/common-history đối ứng LSTM, 1.954 train và 250 validation.

## Khóa trước thực nghiệm

`experiments/configs/cnn_one_step_option_a.lock.json` ghi semantic config và SHA256, baseline YAML SHA256, ba seeds42/123/456, max100/patience10, trần300 epoch, Adam0,001, batch32 và MSE. Validator official tách khỏi validator config chung để không cấm diagnostic ít epoch. Entry point kiểm lock trước runner và mỗi lần tạo loaders, chỉ đổi output paths cho run mới.

Bảy tests chống drift kiến trúc/ngân sách/lr/data/seeds/threads và fingerprint lock sai đã đạt. JUnit logs/audit/tv5_item8_plan_tests.xml. Không đổi source trainer, runner hoặc checkpoint helper trong mục này.

## Quy trình

`scripts/run_tv5_official.py` gọi runner chung với purpose research. Mỗi seed khởi tạo mới theo seed, dùng Adam/MSE/train/validation/early stopping và giữ best validation checkpoint. Sau ba run, nạp lại cả ba checkpoint mặc định không allow_diagnostic, kiểm expected config/provenance/run/seed, finite weights, prediction exact so model RAM và MSE reload bằng best validation loss. Best epoch được đối chiếu toàn history, không lấy epoch cuối mặc định.

Giữ cả ba seed, không chọn seed thắng. Báo mean và std mẫu ddof=1. Không đánh giá hiệu năng test, không so USD với LSTM/persistence trong mục 8. Việc đó thuộc mục 9 phối hợp TV6. Chưa kết luận lợi nhuận hoặc chất lượng ngoài giai đoạn validation.

Source hashes gồm backend/official script/YAML/lock và frozen config được ghi preflight trước run, đối chiếu sau toàn bộ run. Run metadata có CPU/threads/Python/Torch/source hash; thời gian loop và cả runner ghi riêng. Các artifacts cũ giữ nguyên.

## Kết quả thực tế

| Seed | Epoch chạy | Best epoch | Best validation MSE chuẩn hóa | Loop giây | Early stop |
|---|---:|---:|---:|---:|---|
| 42 | 42 | 32 | 0,008859637353239415 | 14,0275 | Có |
| 123 | 51 | 41 | 0,006599455843759253 | 16,3094 | Có |
| 456 | 53 | 43 | 0,008699425860241878 | 16,3464 | Có |

Tổng146/300 epoch, mean best validation MSE 0,008052839685746849, std mẫu ddof1 0,0012612138497237863. Đây là MSE trên giá chuẩn hóa, chưa phải USD hoặc test metric. Không chỉ công bố seed123, giữ cả ba kết quả/checkpoint. Dừng sau 10 epoch không cải thiện, không tiếp tục max100 khi patience đạt.

Cả ba research checkpoint nạp mặc định thành công với expected provenance/model config/training fingerprint/run/seed. Từng prediction validation khớp best model RAM bằng dung sai 0, reload MSE bằng đúng best_val_loss. Trọng số hữu hạn và khác khởi tạo, source/backend/YAML/lock giữ hash qua run. Dữ liệu vẫn 1.954 train/250 validation.

Tổng thời gian loop khoảng46,6833 giây. Runner wall107,6279 giây, process CPU93,4844 giây gồm nạp/kiểm dữ liệu, metadata và checkpoint I/O. Chỉ benchmark local, không suy rộng tốc độ máy khác. Python3.13.7, Torch2.14.1+cpu, torch_threads1, thông tin interop/CPU/máy trong summary và từng run metadata. Chưa đo peak RAM.

Receipt `logs/audit/tv5_item8_20261126T044554616259Z/summary.json`. Thư mục cùng chứa official.yaml, locked_plan.json, preflight.json, results.csv, history_seed*.csv, validation_scaled_seed*.csv, checkpoints và official_overview.png. Notebook05 có21 cells và12/12 code cell đã lưu output, giữ các outputs cũ; receipt notebook_verification.json cùng thư mục.

Semantic fingerprint e78dd9f83140e083d8888005fee93e7667b77404beb9d7479941099192da7fa3. Lệnh tái lập `python scripts/run_tv5_official.py` tạo bộ run mới, không ghi đè artifacts đã chạy. Source/docs/config vào Git theo rule, generated logs/weights tiếp tục lưu local và bàn giao riêng ở mục10.

Mục8 đạt phạm vi thực nghiệm chính thức local. Mục9 mới phối hợp TV6 so sánh CNN/LSTM/persistence cùng mẫu với MAE/RMSE USD. Chưa nghiệm thu toàn bộ TV5 hoặc đánh giá test cuối.
