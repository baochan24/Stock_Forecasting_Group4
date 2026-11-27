# TV5 — lộ trình CNN một bước và thực nghiệm so sánh

## Mục10 — audit/tái lập/bàn giao local

Audit toàn thể đạt162/162 tests. Source tách riêng cũng đạt162/162, forward dữ liệu thật, nạp6 research models và tái tính metrics/monitoring khớp. Đã có setup/consumer docs, payload manifest/checksums và gói local có đầy đủ dependencies. [Audit cuối](TV5_Final_Handoff.md). TV5 đủ10 hạng mục trong phạm vi local; máy nhận và test cuối/API vẫn chưa xác nhận/thuộc TV6. ZIP/receipt cuối theo logs/audit/tv5_item10_latest.json, không upload/push trong tác vụ này.

## Bổ sung monitoring validation sau mục9

Theo yêu cầu người dùng, thêm bốn biểu đồ residual theo ngày/rolling20/phân phối/monthly MAE, bảng bias/P95/tail/top errors và inventory tài nguyên.17/17 tests đạt, phân tích7 runs trên250 dates, không train lại/tuning/test. Notebook05 có14/14 code cell lưu output. Peak RAM train lịch sử và production drift chưa đo/triển khai, được ghi rõ. [Báo cáo monitoring](TV5_Validation_Monitoring.md).

## Mục9 — so sánh validation USD hoàn thành local

Ngày26/11/2026, cùng250 validation IDs/ngày2023 và scaler train, đủ3 seed mỗi mạng. MAE/RMSE USD persistence1,6368/2,1206, CNN mean3,3660/4,3507, LSTM mean2,2494/2,7511; baseline có sai số thấp hơn cả6 model trên validation. Không tuning/chọn seed hoặc đánh giá test. Module dùng chung metric/persistence tối thiểu bổ sung đúng thư mục,12 tests đạt. Notebook05 có13/13 code cell lưu output. [Báo cáo mục9](TV5_Item9_Validation_Comparison.md). Tiếp theo mục10, audit/tái lập/bàn giao; final test vẫn thuộc TV6.

## Mục 8 — ba run chính thức hoàn thành local

Ngày 26/11/2026, khóa phương án A trước run, bảy tests chống drift đạt. Seeds42/123/456 chạy 42/51/53 epoch, tổng146/300, đều early stopping. Best epoch32/41/43, cả ba research checkpoint đã reload khớp MSE và predictions với RAM. Không đánh giá hiệu năng test hoặc chọn seed thắng. [Báo cáo mục 8](TV5_Item8_Official_Experiments.md). Tiếp theo mục 9, phối hợp đánh giá cùng tập mẫu và MAE/RMSE USD.

## Mục 7 — smoke AAPL hoàn thành local

Ngày 26/11/2026, CNN diagnostic seed42 chạy đủ 5 epoch trên 1.954 train/250 validation. Best epoch2, validation MSE chuẩn hóa 0,054332359126796244, reload khớp MSE và từng prediction. Loss/gradients/weights hữu hạn, coverage đủ batch cuối, không đánh giá hiệu năng test. Notebook 05 có bảng và biểu đồ smoke, 11/11 code cell đã có output. [Báo cáo mục 7](TV5_Item7_AAPL_Smoke.md). Tiếp theo mục 8, khóa cấu hình trước official runs ba seed.

## Sơ đồ notebook mục 1–6

Theo yêu cầu người dùng, đã bổ sung bốn sơ đồ nhúng PNG về dữ liệu TV1/TV2/CNN, shape forward, training/validation/selection và checkpoint save/load. Notebook 05 có 17 cells, 10 code cell đã thực thi; giữ output các mục trước, chỉ chạy cell vẽ mới. Sơ đồ diễn giải flow, không biểu thị kết quả train AAPL. Receipt logs/audit/tv5_diagrams_20261126T042128106254Z/summary.json.

## Mục 6 — checkpoint CNN hoàn thành local

Ngày 26/11/2026, đã nối saver/loader CNN có architecture/config fingerprint, weights checksum, dataset/scaler/prepared/source hashes, run/seed và best validation metadata. Diagnostic bị từ chối mặc định, runner persistence có purpose rõ ràng. Bộ hồi quy đạt 138/138, gồm 27 ca checkpoint mới. Notebook 05 chạy 9/9 code cell và lưu output. Chưa train AAPL hoặc nghiệm thu model nghiên cứu CNN thật. [Báo cáo mục 6](TV5_Item6_Checkpoint_Provenance.md). Tiếp theo mục 7, smoke AAPL purpose diagnostic.

## Audit lại mục 1–5 ngày 26/11/2026

Lượt hồi quy mới đạt 111/111 và forward AAPL đạt, config data CNN khớp LSTM đối ứng, trainer TV4 giữ nguyên. Ba điểm theo dõi gồm chưa khóa phương án A ở validator chung, phụ thuộc log TV4 local khi tái lập và câu README cũ. Không phát hiện lỗi chặn mục 6 trong phạm vi đã kiểm. Chưa train AAPL hoặc chứng nhận toàn bộ TV5. [Audit chi tiết](TV5_Items1_5_Audit.md).

## Mục 5 — nối loop chung hoàn thành local

Ngày 26/11/2026, đã thêm factory/config CNN và dispatch trong runner TV4. Giữ nguyên trainer, có RAM diagnostic và từ chối persistence CNN trước run khi chưa có checkpoint helper mục 6. Bộ hồi quy đạt 111/111, gồm chín ca tích hợp mới. Notebook 05 chạy 7/7 code cell, loader thực có 1.954 train/250 validation. Chưa train AAPL. [Báo cáo mục 5](TV5_Item5_Shared_Training.md). Tiếp theo mục 6.

## Mục 4 — nghiệm thu model hoàn thành local

Ngày 26/11/2026, notebook chạy 6/6 code cell, bộ hồi quy CNN/training đạt 102/102 tests. Bốn ca mới kiểm batch 1/32 với gradient và Adam update, dropout train/eval, file state_dict sau cập nhật và strict reload. Không thay model hoặc dữ liệu. [Báo cáo mục 4](TV5_Item4_Model_Acceptance.md). Tiếp theo mục 5, nối CNN vào training loop TV4.

## Mục 3 — kết nối dữ liệu CNN

Consumer dùng lại factory dữ liệu TV4 và reference one-step lookback30/common60. Các ngày, thứ tự ID và X/y được đối chiếu với prepared artifacts, cùng scaler/version đã dùng trong run LSTM. Forward toàn train/validation AAPL bằng CNN CPU float64 đạt. Bộ hồi quy CNN và training đạt 98/98. Chi tiết và receipt notebook được ghi trong báo cáo mục 3 sau khi chạy đầy đủ cells.

Mục 3 đã hoàn thành local, notebook chạy 5/5 code cell và lưu output dữ liệu thật. [Báo cáo và bằng chứng](TV5_Item3_AAPL_Data.md). Tiếp theo là mục 4 theo flow.

## Mục 2 hoàn thành local ngày 26/11/2026

Giữ kiến trúc phương án A, chuyển CPU float64, khóa lookback30/một feature/một output và kiểm config/input/output. Tests CNN đạt 26/26, notebook chạy 4/4 code cell. Precision do agent lựa chọn để đồng nhất với LSTM khi thực hiện mục 2, đã ghi Decision Log. Bước tiếp theo là mục 3, nối dữ liệu TV2. [Báo cáo mục 2](TV5_Item2_Architecture_Contract.md)

## Quyết định phương án A ngày 26/11/2026

Người dùng đã chốt một cấu hình CNN hiện có, ba seed 42/123/456, tối đa 100 epoch/run và patience 10, trần 300 epoch. Kiến trúc dùng để so CNN với LSTM theo Extension của đề. Dtype còn chờ quyết định riêng trong mục 2; chưa đánh dấu mục 2 hoàn thành. Decision Log đã cập nhật.

Trước mục 2, người dùng yêu cầu rà ngân sách để quyết định. Đã lập [sơ khảo ngân sách](TV5_Budget_Preliminary_20261126.md), phân biệt ngân sách TV4 đã chốt với các phương án CNN 3/6/9 run còn là đề xuất. Kiến trúc, dtype và ngân sách TV5 chưa được chốt trong lần rà này.

## Mục 1 hoàn thành local ngày 26/11/2026

Đã tiếp nhận nguyên nội dung ba file model/exports/tests từ PR #9. Baseline 7/7 tests đạt từ workspace, notebook 05 chạy 4/4 code cell và lưu output. Source tiếp nhận khớp SHA256 và các file TV1–TV4 được bảo vệ giữ nguyên. Dùng môi trường TV4 đã kiểm chứng và kernel riêng TV5. [Báo cáo mục 1](TV5_Item1_Source_Intake.md)

Bước tiếp theo là mục 2, chốt kiến trúc, dtype và contract. Các bảng kế hoạch phía dưới phản ánh thời điểm lập trước khi tiếp nhận.

## Cập nhật sau TV4 ngày 26/11/2026

TV4 đã hoàn thành local và push nhánh TV4. Đã kiểm tra lại PR #9/head edc2bd953c7644040f4142a545316377cd143e13 của TV5, vẫn open/chưa merge, source chưa thay đổi. Tests CNN nguyên nhánh chạy lại 7/7 đạt. TV5 hiện có model unit-level, chưa tích hợp vào workspace hoặc train AAPL. [Audit và flow cập nhật 10 mục](TV5_PR9_Review_20261126.md)

Mục tiếp theo là 1, tiếp nhận chọn lọc source CNN và tạo notebook TV5. Từ mục 3 phải dùng cùng 1.954 mẫu train và 250 validation với LSTM lookback 30. Kiến trúc/dtype CNN và ngân sách thực nghiệm cần chốt ở mục 2. Những ghi nhận chờ TV4 ở phần kế hoạch cũ bên dưới đã được thay thế bằng trạng thái hiện tại.

Ưu tiên cập nhật25/11/2026 theo người dùng: **hoàn thành TV4 trước rồi mới triển khai TV5**. Theo dõi `reports/audits/TV4_Progress.md`; toàn bộ mục TV5 dưới đây vẫn là kế hoạch, chưa bắt đầu.

Lập ngày 25/11/2026 theo yêu cầu người dùng sau audit. **Đây là kế hoạch; chưa tiếp nhận source TV5 vào backend workspace chính hoặc hoàn thành các mục dưới đây.** Cơ sở: `reports/audits/TV4_TV5_PR9_PR10_Audit_20261125.md`, rule.md, đề Topic4, docs/01/03/04/10/11/12 và handoff TV3.

## Đích cần đạt

CNN một bước nhận cùng lịch sử30 phiên AAPL và dự báo cùng target với LSTM; dùng dữ liệu/scaler TV2 và training loop chung TV4. Cung cấp model, checkpoint/config có provenance, logs thực nghiệm, notebook và kết quả phối hợp đánh giá. Không đặt điều kiện CNN phải thắng LSTM/persistence.

Nguồn dự kiến tiếp nhận: PR #9, nhánh TV5, commit `edc2bd953c7644040f4142a545316377cd143e13`. Audit độc lập đã chạy7/7 unit tests; chưa có bằng chứng train AAPL. Đây không phải trạng thái triển khai workspace chính.

## Flow cố định

| Mục | Công việc | Đầu ra và điều kiện nghiệm thu | Phụ thuộc/trạng thái |
|---|---|---|---|
| 1 | Tiếp nhận source CNN đúng module và lập baseline | Nhận model/__init__/tests từ commit đã kiểm tra vào backend/models/cnn_one_step và tests/models; chạy lại7 tests từ workspace; ghi môi trường/source hashes. Ghép nội dung báo cáo CNN, không thay cả báo cáo TV3/TV4 | Chưa bắt đầu; có thể làm ngay |
| 2 | Chốt kiến trúc, dtype và contract | Đề xuất CNN17.057 tham số, input(B,30,1), output(B,1), một feature, dropout; đối chiếu LSTM4.513 tham số và ngân sách. Chốt dtype tường minh và ghi Decision Log trước khi thay kiến trúc/precision | Sau1; quyết định chưa tự coi đã duyệt |
| 3 | Kết nối dữ liệu TV2 với CNN | Consumer/adapter input-only và training X/y, kiểm IDs/ngày/version/hash/scaler; transpose trong model chỉ thay chiều, không thay thứ tự mẫu. Xác nhận train/validation và coverage contracts; không refit scaler | Sau2; độc lập loop TV4 |
| 4 | Nghiệm thu cấu hình và model | Kiểm giới hạn config một bước, shape/dtype/device, input hữu hạn ở ranh giới phù hợp, batchB1, train/eval/dropout, gradients hữu hạn và Adam update; state_dict lưu/nạp file thật giữ output eval. Tests kiểm lỗi thực tế, không chỉ lặp implementation | Sau3; dùng tensors tổng hợp cho kiểm gradient |
| 5 | Nối CNN vào training loop chung TV4 | Factory/config CNN chạy Adam/MSE, weighted epoch loss, validation no_grad, early stopping; không có training loop thứ hai. Kiểm cấu hình model/horizon và giữ batch cuối | Sau4; CHỜ TV4 sửa import/dtype và interface artifacts |
| 6 | Hoàn thiện checkpoint CNN và provenance cùng artifacts/TV6 | Config đủ tái tạo CNN, state/hash/dtype/dataset/scaler/run/seed/best_epoch, validation selection. Reload instance mới từ file thật, so output; từ chối nhầm config/data/scaler và diagnostic chưa train theo contract được thống nhất | Sau5; helper checkpoint LSTM hiện không nhận CNN |
| 7 | Smoke run AAPL bằng train/validation | Run ngắn có giới hạn đã ghi, loss/gradient/weights hữu hạn, CSV/biểu đồ loss, thời gian CPU và reload/validation nhất quán. Gắn nhãn diagnostic, không đưa checkpoint này thành model cuối | Sau6; không đánh giá test |
| 8 | Chạy thực nghiệm CNN chính thức | Chốt seeds/ngân sách bằng validation và đo CPU; chạy3 seeds định trước, best checkpoint từng seed, config/hash/logs/thread/time/số tham số, khóa cấu hình trước test. Cấu hình khởi đầu batch32/Adam0.001/MSE/max100/patience10 là điểm xuất phát, không tuyên bố tối ưu | Sau7; seeds42/123/456 từ PR TV4 là đề xuất cần đối chiếu/chốt |
| 9 | Phối hợp TV6 so sánh CNN/LSTM/persistence | Cùng sample IDs/target dates/scaler/split/lookback30; MAE/RMSE USD, từng seed và mean/std theo quy ước chốt, train/inference timing cùng điều kiện. TV5 cung cấp runs CNN và phân tích; TV6 dùng module đánh giá chung | Sau8 và có runs LSTM TV4; chưa tính metric test để tuning |
| 10 | Môi trường tái lập, tài liệu và bàn giao | Dependencies/lock phù hợp, lệnh setup/test/run/reload, source và artifacts tách biệt, checksum, notebook đủ outputs, báo cáo triển khai/so sánh/giới hạn. Kiểm bản sao độc lập, ghi riêng xác nhận máy khác và tiếp nhận TV6 | Sau9 để chốt đầy đủ; tài liệu cập nhật xuyên suốt |

Mục1–4 có thể tiến hành trước khi TV4 hoàn chỉnh. Không đánh dấu mục5–8 hoàn thành nếu chưa nối được loop và persistence thật; không tạo loop CNN riêng để né phụ thuộc. Trong mục1 chuẩn bị môi trường đủ chạy baseline; mục10 mới nghiệm thu đầy đủ khả năng tái lập/handoff, không để đến cuối mới ghi môi trường.

## Notebook và báo cáo sau mỗi mục

Khi bắt đầu thực hiện mục1, tạo `notebooks/05_TV5_CNN_Development_and_Experiments.ipynb`, cập nhật builder/executor trong scripts theo cơ chế hiện có. Mỗi mục có giải thích mục tiêu/input/output, code gọi backend/scripts, assertions/bảng/biểu đồ và outputs thật. Không tạo notebook rỗng ở bước lập kế hoạch; không chép pipeline training vào notebook.

Sau mỗi mục: cập nhật mục tương ứng trong báo cáo này, README module và FILE_STRUCTURE khi cần; chạy cells bị ảnh hưởng và lưu outputs tại workspace trước chia sẻ. Không ghi TV5 vào notebook TV1/TV2/TV3 hoặc ghi đè phần báo cáo của thành viên khác. Mục chưa làm ghi chờ, không gán pass từ kết quả audit nhánh khác.

## Những điểm phải giữ xuyên suốt

- Snapshot/scaler/prepared TV2 được accept và bất biến; split theo target: train2015–2022, val2023, test2024–2025. CNN chỉ làm một bước, không tự mở rộng năm bước.
- TV2 arrays hiện float64 và TV3 LSTM float64. Đề xuất dùng CNN float64 để đồng bộ đường dữ liệu/điều kiện benchmark; đây chưa phải quyết định đã được duyệt. Nếu chọn float32 cần adapter/copy/tolerance và báo rõ khác biệt, không sửa source arrays.
- Thí nghiệm lookback10/30/60 của LSTM được phối hợp TV4; so sánh CNN chính theo lookback30 đã chốt, không tự nhân thêm các run CNN ngoài ngân sách.
- Chọn checkpoint/config bằng validation; test dành cho đánh giá cuối sau khi khóa cấu hình. Kiểm schema/coverage của test không đồng nghĩa đo chất lượng dự báo.
- Độ chênh tham số không tự là vi phạm; phải báo chính xác và ghi ngân sách tuning, dtype, CPU/thread và cách đo. Không điều chỉnh CNN chỉ vì thấy kết quả test.
- Không tự upload/push/merge hoặc nhắn thành viên trong bước lập lộ trình này. Người dùng sẽ giao tiếp từng mục; các thay đổi quyết định thiết kế được ghi rõ trước triển khai.

**Bước tiếp theo theo flow: mục1 — tiếp nhận source CNN đúng module và kiểm chứng baseline tại workspace.**
