# Phân công nhóm sáu thành viên — dữ liệu, model và huấn luyện

Trạng thái: phân công theo vai trò TV1–TV6, chưa gắn tên hoặc tài khoản cá nhân. TV6 là nhóm trưởng. Không tự tạo branch, issue hoặc giao việc qua tin nhắn.

## Nguyên tắc
- Cả sáu thành viên tham gia phần nghiên cứu liên quan dữ liệu, mô hình, huấn luyện, đánh giá.
- API và front-end do TV6 — nhóm trưởng phụ trách riêng, không chia cho TV1–TV5.
- Mọi người ghi cấu hình, logs, audit và bằng chứng; không điền kết quả trước khi chạy.
- Thay đổi interface dữ liệu/model cần thống nhất trước khi tích hợp.

## Trách nhiệm và bàn giao

| Thành viên | Phần chính | Vị trí làm việc | Bàn giao và kiểm tra |
|---|---|---|---|
| TV1 | Thu thập, kiểm tra và mô tả dữ liệu AAPL | backend/data/acquisition, backend/data/validation; data/raw, validated, metadata | Snapshot/hash, chính sách điều chỉnh, thiếu/trùng và xử lý; báo cáo dữ liệu có bằng chứng |
| TV2 | Tiền xử lý, chia tập, scaler, windowing một/năm bước | backend/data/preparation, backend/data/transforms; tests/data | Hợp đồng input/target/ngày/split, scaler train, số mẫu; đối chiếu cửa sổ bằng tay và audit rò rỉ |
| TV3 | LSTM một bước và LSTM direct multi-output năm bước | backend/models/lstm_one_step, backend/models/lstm_multi_step, backend/model_trace; tests/models | Forward đúng shape, khởi tạo trạng thái độc lập; kiểm tra output; trace thực chỉ công bố sau đối chiếu |
| TV4 | Training/validation và thực nghiệm LSTM | backend/training, backend/experiments/runner, backend/experiments/management; experiments/configs, runs; tests/training | Training loop dùng chung, Adam/MSE, early stopping, checkpoint tốt nhất; loss logs, seed, đo CPU và kết quả validation |
| TV5 | CNN 1D một bước và thực nghiệm so sánh | backend/models/cnn_one_step; cấu hình/run CNN; tests/models | Đề xuất kiến trúc CNN nhỏ trước triển khai; dùng training loop TV4, cùng lookback 30/ngày đánh giá; ghi tham số, ngân sách và thời gian |
| TV6 — nhóm trưởng | Baseline, inference nghiên cứu, đánh giá, phân tích lỗi và tích hợp model/train | backend/baselines, backend/inference, backend/evaluation, backend/error_analysis, backend/artifacts, backend/audit; tests/evaluation, integration | Persistence tính tay; metric một/năm bước, từng seed; checkpoint/scaler đúng bộ; audit tích hợp, release và tổng hợp báo cáo |

TV3 và TV4 cùng kiểm tra LSTM multi-step: TV3 chịu kiến trúc/forward, TV4 chịu train/validation. TV5 dùng loop chung, không tự viết pipeline train thứ hai. TV6 phụ trách integration không đồng nghĩa tự thực hiện lại mọi phần thành viên.

## Thứ tự phối hợp
1. TV1 cung cấp dữ liệu/metadata cho TV2.
2. TV2 công bố mẫu và shape cho TV3, TV4, TV5; TV6 kiểm tra baseline/ngày.
3. TV3 và TV4 hoàn thiện một run LSTM một bước; đo CPU trước mở rộng.
4. TV5 thử CNN, TV3/TV4 thực hiện multi-step; khóa cấu hình bằng validation trước test.
5. TV6 điều phối đánh giá cuối và bộ phát hành; mọi thành viên kiểm tra phần mình và bổ sung bằng chứng.

## Tài liệu và báo cáo
- TV1 chủ trì reports/02_Data_Description.md.
- TV2 bổ sung preprocessing và audit dữ liệu vào báo cáo triển khai/dữ liệu.
- TV3 mô tả kiến trúc/forward, TV4 training/checkpoint, TV5 CNN và phép so sánh trong reports/03_Implementation.md và reports/06_Baseline_and_Model_Comparison.md.
- TV6 tổng hợp vấn đề/phạm vi, kết quả và giới hạn; mỗi thành viên đóng góp lỗi/giới hạn thực tế của phần mình.
- Hướng dẫn chạy nghiên cứu do người triển khai từng phần bổ sung; TV6 tích hợp hướng dẫn toàn hệ thống và phần trình diễn.

## API và front-end — nhóm trưởng xử lý
TV6 phụ trách backend/api, backend/services/results, frontend và phần web của docs/09_Setup_and_Run.md, reports/05_System_Demonstration.md. Phần này là trách nhiệm riêng của nhóm trưởng, không phân vào workload model/train của TV1–TV5. Giao diện dùng model đã train, không yêu cầu người xem train lại.

## Điều kiện bàn giao chung
- Có mô tả thay đổi, input/output và hướng dẫn chạy thật khi implementation đã có.
- Có test/audit phù hợp và logs; chưa chạy phải ghi rõ chưa chạy.
- Không dùng test để tuning; không chọn seed thắng test.
- Không commit dataset/checkpoint/logs sinh ra trái chính sách .gitignore; ghi cách nhận artifacts.
- Không thay Define/Design hoặc mở rộng mục tiêu nếu chưa thống nhất.
- Chưa đặt deadline, tài khoản reviewer hoặc branch cụ thể khi nhóm chưa cung cấp.
