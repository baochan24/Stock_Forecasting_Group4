# Hoàn thành hạng mục kiểm chứng và chốt ứng viên LSTM

Hoàn thành local ngày27/11/2026 theo yêu cầu **không train thêm hoặc tạo kiến trúc mới**. Đã tổng hợp các phiên bản, khóa bộ ứng viên, chốt protocol đánh giá, kiểm đường dự báo và audit độc lập. Hạng mục này hoàn thành trong phạm vi nghiên cứu; chưa phải release/API/demo hoặc chứng minh hiệu quả độc lập trên tương lai.

## 1. Ứng viên được giữ

Giữ **LSTM residual, last-hidden readout**, một bước và direct5bước, đủ seeds42/123/456. Sáu checkpoint đã huấn luyện trước đây trêntrain2015–2022, bestcheckpoint chọn bằngvalidation2023. Không chọn seed thắngtest. Fold2022 chỉ là kiểm tra development/độ ổn định, không đưa vào catalog ứng viên cuối.

Registry `experiments/configs/tv6_lstm_residual_candidate_v1.json` ghi rõ representation, công thức decode, model/seed/horizon/bestepoch, scalerID và hashmanifest/state/scaler. Registry được tạo trước forward test, có semanticSHA và không tự ghi đè nếu nội dung khác. Đây là registry ứng viên nghiên cứu, không thay `tv6_evaluation_protocol_v1.json` hoặc FrozenForecaster v1.

Meanreadout chỉ là thử nghiệm được lưu, không được chọn vì không cải thiện nhất quán. LSTM v1 được bảo toàn cùng kết quả test ban đầu, không xóa hoặc thay điểm bằng kết quả của residual.

## 2. Kiểm đường dự báo, không thay trọng số

Rawhistory→(history−origin)/scale_train→LSTM checkpoint→delta chuẩn hóa→origin+scale_train×delta→giáUSD. Mean của scaler không cộng vào delta. H5 là năm đầu ra cùng origin, không cộng dồn recursive hoặc dùng actual làm input.

Đã kiểm12pipeline validation (2fold×2mode×3seed) và6pipeline đánh giá test. Scalerfit/partialfit bị chặn bằngspy; chỉ nạp artifact có liên kếtdataset/source. Model CPUfloat64,eval,no-grad,requires_gradFalse. State/hash trước/sau không đổi. Batch32 giữ batchcuối; mẫu đầu/cuối chạy riêng khớp fullbatch trongatol1e-12USD.

Inputdates/giá khớp snapshot, actual ghép sau input-only forward; validationpredictions khớp output đã lưu. Test502mẫu h1 và498windows h5 khớp đầy đủcohort keys/hash đã khóa. Không loại mẫu/outlier hoặc làm tròn trướcmetric. Không fit/refit/train/optimizerstep hoặc sinh checkpoint mới.

## 3. Protocol đánh giá sau phát triển

Test2024–2025 đã được quan sát trước khi thiết kế residual. Vì vậy lần đánh giá ứng viên này được khóa nhãn **post-development evaluation on previously observed test**, `independent_holdout=false`. Chỉ dùng sáu model đã có, đủba seed, baseline trên cùngmẫu, MAE/RMSEUSD từnghorizon/overall vàmean/std mẫu. Không tuning/chọn lại seed sau kết quả.

Đây là đánh giá ứng viên trên giai đoạn test cũ, không phải một test độc lập mới và không sửa lịch sử thực nghiệm. Nếu sau này nghiên cứu thêm phải có protocol riêng; không dùng bảng này để tiếp tục tìm hyperparameter thắng.

## 4. Kết quả chốt ứng viên

Trung bình ba seed, USD; H5overall flatten498×5lỗi trướcmetric:

| Phương pháp | H1 MAE | H1 RMSE | H5overall MAE | H5overall RMSE |
|---|---:|---:|---:|---:|
| LSTM residual — đánh giá sau phát triển | **2,465892** | **3,652078** | **4,607636** | **6,682840** |
| Persistence — cùngmẫu | 2,476989 | 3,654583 | 4,632497 | 6,707243 |

Std mẫu LSTM: H1MAE0,000741/RMSE0,000340; H5overallMAE0,001169/RMSE0,005690. MAE thấp hơn persistence khoảng0,45% ởh1 và0,54% ởh5; RMSE khoảng0,07% và0,36%. Đây là chênh lệch nhỏ, chưa có significance hoặc threshold thực tiễn đã khóa, không chứng minh vượt baseline bền vững.

Đối chiếu v1: kết quả test ban đầu LSTM h1MAE10,896342/RMSE14,031708; h5overall12,603942/16,155448USD. Bản residual có số liệu thấp hơn rõ trên cùng giai đoạn/mẫu, nhưng được phát triển sau khi xemtest: **không diễn giải chênh lệch này như một so sánh độc lập không thiên lệch**. Bảngcomparison.csv giữ riêng phase gốc vàpost-development. Các điểm development2022/2023 cũng nằm riêng, không trộn thànhtest.

Mục6 đã cho thấy đóng góp của lịch sử còn yếu ở một sốfold và gần mức điều chỉnh hằng số; lần chốt này không xóa giới hạn đó. Không suy kết quả thành quy luật cổ phiếu hoặc lợi nhuận giao dịch.

## 5. Audit và đầu ra hoàn thành

- 18 kiểm tra pipeline thật, đủ 12 validation và 6 test cases, không thay seed/cấu hình.
- Audit độc lập đạt 84 metric rows/21 aggregates/23.832 prediction rows: full calendar keys, actual/origin khớp raw, baseline đúng, metric bằng math.fsum/sqrt và std bằng statistics. Hash config/source/scaler/checkpoint và protocol v1 không đổi.
- Notebook06 hiện 38 cells/19 code cells có output; thêm registry/bảng phase/từng seed/horizon, kiểm tra pipeline và biểu đồ. Builder đồng bộ, giữ output trước. Run All chỉ đọc kết quả, không forward/train lại.
- Receipt `logs/audit/tv6_lstm_completion_20261127T023617456097Z/summary.json`; execution journal, independent_audit, CSV/PNG và notebook_verification cùng folder.
- CLI thực thi `scripts/complete_tv6_lstm_candidate.py` tạo audit mới nếu chạy lại; để tái kiểm không forward dùng `scripts/audit_tv6_lstm_completion.py`.

## 6. Quyết định và bàn giao sang bước tiếp theo

Hoàn thành hạng mục kiểm chứng/chốt ứng viên trong giới hạn không train thêm. Giữ sáu residual-last checkpoints làm bộ ứng viên để bàn giao mục7; không tự promote catalog chính thức. Chưa tạo API hoặcweb, chưa xác minh máy thành viên khác, chưa có bằng chứng holdout độc lập cho residual.

Khi triển khai mục7, bắt buộc giữ đúngrepresentation/scaler/checkpoint vàdecode delta. Không nạp residual vào đường inverse absolute-price củav1 hoặc đổi tên outputdelta thànhgiáUSD trực tiếp. Mục7 sẽ kiểm release/integration end-to-end riêng; mục8–10 tiếp tục theo flow. Không cần thêm vòng train để đọc notebook hoặc thực hiện bàn giao bộ hiện có.
