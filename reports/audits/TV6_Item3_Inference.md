# TV6 mục3 — nghiệm thu inference/persistence local

Theo yêu cầu làm việc cẩn thận và kiểm liên tục, đã đối chiếu rule/đề/contracts/module boundaries và protocol đã audit trước sửa. Chỉ làm inference validation, không mở rộng evaluation/test/API/frontend.

## Thực hiện

FrozenForecaster dùng protocol/registry mỗi request, adapter input-only TV3, scaler đã accept và9 model catalog. Kiểm lịch sử snapshot từng input, model CPU64/eval/frozen, inference_mode/batch32/tail, inverse USD. Một bước lstm/cnn/persistence, năm bước lstm direct/persistence. Không target/y/path/scaler từ request, không actual/metric trong output. Calendar theo phiên snapshot; test dates chặn trước forward.

Nguồn CNN expected metadata được đọc từ manifest đã pin hash/provenance bằng protocol trước, không tin file tự khai ngoài catalog. LSTM loader kiểm identity/mode/hash, guard đối chiếu run/seed/config với catalog trước load. Trọng số không cập nhật hoặc serialize lại. Artifact/source hashes được đối chiếu trước/sau kiểm đầy đủ.

## Kết quả

69/69 tests đạt, gồm24 integration inference và45 evaluation/protocol; JUnit logs/audit/tv6_item3_tests.xml. Các test là validation input probes hoặc fixture rejection, không có test model predictions. Đã kiểm66 tests ở lượt đầu rồi chạy lại69 sau bổ sung runtime/no-fit/guard-before-forward, không dùng lượt đầu thay chứng nhận cuối.

Script full-validation đã kiểm9 models và2 baseline modes,11 method/mode/seed checks,6.670 prediction rows. Một bước250 samples:6 neural runs×250 +250 persistence =1.750 rows. Năm bước246 samples:3 LSTM runs×246×5 +246×5 persistence =4.920 rows. Không nhân baseline theo3 seeds. Đúng dates/sample/horizon và finite USD, khớp neural direct call từstoredX NPZ trong rtol/atol1e-12, persistence bằng rawlast chính xác. Batch tail một bước26/năm bước22 được giữ.

Receipt logs/audit/tv6_item3_20261126T164900357232Z/summary.json, checks.csv và validation_inference_usd.csv cùng thư mục. Không tính loss/MAE/RMSE mới hoặc join actual. source_artifacts_unchanged=True, không thay protocol/registry hoặc checkpoint/scaler/snapshot.

Notebook06 bổ sung mục3 với checks/bảng dự báo seed42/hình1 và5 bước, không actual/metric. Nội dung cũ giữ outputs; top status cập nhật tới mục3. Hướng dẫn docs/TV6_Inference_Contract.md.

Notebook đã chạy thành công, tổng10 cells/5 code cell có output, ảnh inference_examples.png và notebook_verification.json cùng thư mục receipt. Max absolute difference của cả11 checks thực tế bằng0, không chỉ nằm trong dung sai.

## Giới hạn và bước sau

Historical validation scope, không test/live quote/future ngoài snapshot; release_id=None trước mục7. Guard hash mỗi request có overhead, không đưa ra cam kết production latency. Chưa API/frontend hoặc acceptance máy khác. Mục4 tiếp theo hoàn thiện evaluation USD/per-horizon/alignment, trước mục5 final test. Không coi inference đạt là model vượt baseline hoặc toàn bộproject đã hoàn thành.
