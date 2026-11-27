# TV6 mục2 — khóa protocol đánh giá cuối

Ngày26/11/2026. Hoàn thành trong scope yêu cầu người dùng, dựa trên rule/đề/project/module contracts/decision log và intake dữ liệu đã kiểm lại. Không inference/model metrics trên test, không train hoặc triển khai frontend.

## Nội dung đã khóa

- 9 accepted checkpoints, đủ seeds42/123/456 của LSTM1/LSTM5/CNN1, cùng snapshot/scaler và lookback30.
- Test target split2024–2025 với502 mẫu một bước và498 windows năm bước, ordered IDs/origin/target-date cohort hashes và120 artifact/source hashes từ intake.
- MAE/RMSE USD từng seed/horizon, mean/std mẫu ddof1, không làm tròn trước metric/không ensemble. Baseline deterministic, same sample comparison. Overall h5 flatten residuals, không mean horizon RMSE.
- CPU float64/thread1/batch32, không shuffle/drop_last, weights/scaler cố định, history rolling đã quan sát, h5 direct output.
- Demo seed42 cố định cho cả ba nhóm neural, agent áp dụng mặc định minh bạch trong scope mục2, không gán là seed tốt nhất hoặc câu chọn trực tiếp từ người dùng. Không automatic test winner default.
- No retrain/refit/test tuning hoặc seed/checkpoint selection theo test. Drift artifacts/cohort/policy làm lock không hợp lệ; thay đổi cần version có lý do. Numeric tie1e-12USD không phải practical/statistical significance.

File máy đọc experiments/configs/tv6_evaluation_protocol_v1.json, hướng dẫn docs/TV6_Final_Evaluation_Protocol.md. Semantic SHA256 9e81b5ca4f3ae9ddfd5969d846458afbf87e95ea89be98ddb8349a4906119579. Tạo một lần, lệnh chạy lại chỉ verify lock, không ghi đè drift.

## Kiểm chứng

9/9 tests protocol đạt, gồm chặn đổi demo seed/ddof/rounding/dtype/no-test-tuning dù đã rehash, đổi cohort, fingerprint hỏng và artifact bị thay. Tests sử dụng protocol/intake thật; fixture corruption không sửa root data. JUnit logs/audit/tv6_item2_tests.xml. Receipt lock logs/audit/tv6_item2_20261126T162805091988Z/summary.json.

Notebook06 bổ sung mục2 với bảng9 models/cohorts/demo/metric/policy và fingerprint, giữ output mục1/kiểm lại dữ liệu. Không mở rộng thành đánh giá test hoặc release. Thông tin dataset schema được đọc để khóa cohorts, không sử dụng giá để chọn policy/model.

Notebook đã chạy cell mục2 thành công, tổng6 cells/3 code cell có output. Receipt notebook_verification.json nằm cùng thư mục receipt lock mục2, các outputs cũ được giữ nguyên.

Mục3 tiếp theo là inference/persistence. Mục4 hoàn thiện evaluation trước mục5 final test. Practical significance threshold, máy người nhận/production và các hạng mục còn lại không được coi hoàn thành từ lock này.
