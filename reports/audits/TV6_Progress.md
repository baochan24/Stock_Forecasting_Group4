# TV6 — nghiệm thu nghiên cứu và tích hợp coursework

**Hoàn thiện sau mục10 — 28/11/2026:** cài venv mới từ lock thành công,85 pins/pip check,62 tests API/handoff,14 checks Chrome/5 tests JS đạt. Có công cụ xuất biên bản,checker portable,3 bảng CSV và quy trình thành viên nghiệm thu máy khác. Notebook58cells/29code cells,giữ output nghiên cứu. [Báo cáo hoàn thiện](TV6_Closure_and_Handoff.md). Chưa có biên bản từ máy khác,quyền phân phối dữ liệu hoặc xác nhận thủ tục nộp cuối.

**28/11/2026 — mục10 đã audit kỹ thuật local:** đối chiếu đề và10 nội dung đăng ký, cập nhật7 phần báo cáo, kiểm lại dữ liệu/scaler/windows/hash/metrics và regression, notebook56cells/28code cells. Bổ sung gói runtime web local/verifier; vẫn chờ fresh install/máy khác,quyền phân phối dữ liệu và thủ tục nộp cuối. [Kết quả audit](TV6_Item10_Final_Audit.md), [đầu ra theo đề](../../docs/TV6_Coursework_Output_and_Defense.md). Không gọi tất cả điều kiện bàn giao đã đạt.

**Mới nhất — mục9 hoàn thành local:** AAPL Forecast Lab theo concept, API thật;5 tests JS/14 checks Chrome desktop/mobile/outage đạt. Notebook52cells/26code cells. [Nghiệm thu](TV6_Item9_Frontend.md), [cách chạy](../../docs/TV6_Frontend_Demo.md). Mục10 chờ. Bên dưới là lịch sử từng bước.

**Mới nhất — mục8 hoàn thành local:** FastAPI/Uvicorn đủ12route,46tests và15HTTPchecks thật đạt;69corepinsgiữnguyên,khôngtrain. Notebook46cells/23code cells cóoutputAPI/metrics/trace. [Nghiệm thu API](TV6_Item8_API.md), [cách chạy](../../docs/TV6_API_Setup_and_Contract.md). Mục9–10 cònchờ.

**Mới nhất — mục7 hoàn thành local:** release aapl-research-residual-v1,9model/persistence,14tests/22nhómE2E/20.144predictionrows khớp bằng0, ZIP nguồn riêng cùngmáy đạt. Notebook42cells/21code cells cóoutput. [Nghiệm thu mục7](TV6_Item7_Release_Integration.md). Mục8–10 cònchờ; khôngtrain/API/frontend mới.

**Trạng thái hiện tại:** đã hoàn thành chốt ứng viên LSTM trong giới hạn không train thêm. Registry sáu residual-last checkpoint được khóa;18kiểm tra pipeline vàaudit84metrics/21aggregates/23.832predictions đạt. Đánh giá residual trên testcũ được ghi riêng làpost-development, khôngđộc lập. Notebook38cells/19code cells cóoutput. [Báo cáo hoàn thành](TV6_LSTM_Candidate_Completion.md). Chưa promote/release; tiếp theo mục7 khi được giao.

Ablation readout h1 đã hoàn tất6run: không chọn meanreadout vì lỗi kém ở2022 và chỉ nhỉnh rất ít ở2023. Giữ last residual; không testforward/promote. Hai tests/audit độc lập đạt, notebook34cells/17code cells cóoutput. [Kết quả và quyết định](TV6_Readout_Ablation.md).

Sau mục6, ưu tiên1 đã hoàn thànhlocal: tham chiếu drift chỉfittrain và108gradientprobes,7tests/audit độc lập đạt. Chưa thay model/checkpoint hoặc trainablation mới. Notebook06 hiện30cells/15code cells cóoutput. [Kiểm đường học và hướng sửa](TV6_LSTM_Learning_Check.md). Mục7–10 vẫn chờ.

## Kiểm lại bộ dữ liệu bàn giao sau mục1

Theo yêu cầu người dùng, audit sâu toàn bộ window/inverse/scaler và ZIP đã đạt.120 inventory hashes,45 data/scaler files trong ZIP và provenance9 checkpoint khớp. Không thay file hoặc tính test performance. Notebook06 có cell kiểm lại dữ liệu. [Báo cáo](TV6_Data_Recheck.md). Tiếp theo vẫn là mục2 theo flow.

Leader đảm nhận TV6 theo người dùng. Flow cố định bên dưới dùng lại TV1–TV5, không làm lại training. Từ mỗi mục ghi notebook06 và audit riêng. Frontend bám concept đã chốt trong Decision Log khi tới mục9, chưa triển khai trước.

| Mục | Công việc | Trạng thái |
|---|---|---|
| 1 | Audit/tiếp nhận snapshot, scaler, prepared, checkpoints TV1–TV5 | Đạt nghiệm thu local,9 models/120 files |
| 2 | Khóa protocol final evaluation/model chọn cho demo trước test | Đạt local; audit sau sửa có28 tests protocol,45 tests evaluation/protocol |
| 3 | Inference/persistence một/năm bước | Đạt validation local,69 tests,9 model/6.670 prediction rows |
| 4 | Evaluation alignment/USD/per-horizon dùng chung | Đạt validation local; audit sau sửa104 tests,31 metrics/8 aggregates |
| 5 | Đánh giá test2024–2025 các model đã khóa | Đạt local;9 models,13.474 predictions,31 metrics/8 aggregates; persistence tốt nhất |
| 6 | Phân tích lỗi, giới hạn và kết luận nghiên cứu | Hoàn thành phân tích local;4tests/12checkpoint probes/audit đạt. Đã báo vấn đề, chờ sửa theo người dùng trước mục7 |
| 7 | Release manifest, integration và end-to-end | Đạt local:14tests,20.144predictions khớpaccepted,ZIP nguồnriêng; chưa máy khác |
| 8 | API theo contract, health/readiness | Đạt local:46tests/15HTTPchecks,12route,sidecarreadonly; chưafrontend/máykhác |
| 9 | Frontend/demo theo concept AAPL Forecast Lab | Đạt local:5 tests JS/14 checks Chrome/API,desktop/mobile/outage; chưa deployment/máy khác |
| 10 | Audit cuối/tái lập/báo cáo/bảo vệ coursework | Đã audit/tổng hợp local và chuẩn bị runtime handoff; chờ xác nhận máy khác/quyền dữ liệu/thủ tục nộp |

Mục1 không phải phát hành release, quyết định demo seed hoặc đánh giá test. Module metric/persistence/monitoring tối thiểu đã có từ TV5, cần tiếp nhận và hoàn thiện theo phạm vi TV6. Live AAPL chỉ là định hướng mở rộng, chưa chốt nguồn/quyền/data contract để triển khai.

Mục1 đã kiểm snapshot/scaler/prepared, source official CNN hashes, selected lookback30 TV4, best epoch/history/run/seed và reload9 model bằng input validation. Inventory có120 relative paths/hash, file nguồn/dữ liệu được kiểm không đổi. Receipt logs/audit/tv6_item1_20261126T160646012874Z/inventory.json, bản danh mục reports/audits/TV6_Input_Inventory.json. [Báo cáo mục1](TV6_Item1_Input_Acceptance.md). Tiếp theo mục2.

Mục2 đã khóa9 accepted models,3 seeds, cohorts test502/498, USD metrics/per-horizon/mean/std, CPU64 và demo seed42 cố định, không test tuning.9/9 tests đạt, notebook06 có6 cells/3 code cell lưu output. [Protocol](../../docs/TV6_Final_Evaluation_Protocol.md), [báo cáo mục2](TV6_Item2_Protocol_Lock.md). Chưa đánh giá hiệu năng test. Tiếp theo mục3.

Audit bổ sung sau yêu cầu kiểm lại các điểm khóa đã sửa explicit guards/types,root/pinned paths,manifest linkage/full cohort coverage vàregistry lifecycle.45/45 tests đạt, giữ nguyên bytes protocol v1 và các lựa chọn nghiên cứu. Notebook06 có8 cells/4 code cell lưu output, chưa đánh giá test. [Phát hiện và sửa](TV6_Protocol_Audit_and_Fixes.md). Không còn phát hiện chặn mục3 trong phạm vi đã kiểm; end-to-end enforcement tiếp tục ở mục3–5.

Mục3 đạt validation inference/persistence, protocol guard trướcforward, inputs-only/history/CPU64/no-fit/no-grad, schema USD và dates theo phiên.69/69 tests, full-validation9 models/2 baseline modes khớp storedX direct inference và baseline rawlast. Test inference vẫn chặn, release/API/frontend chưa triển khai. [Báo cáo mục3](TV6_Item3_Inference.md), [contract](../../docs/TV6_Inference_Contract.md). Tiếp theo mục4.

Mục4 đạt strict ordered alignment/context, MAE/RMSE USD từng horizon/overall, sample/error counts vàseed mean/std ddof1.101 tests đạt, validation31 metric/8 aggregate/6.670 residual rows, h1 khớp TV5. Notebook06 có bảng/biểu đồ và trạng thái tới mục4. [Báo cáo](TV6_Item4_Evaluation.md), [contract](../../docs/TV6_Evaluation_Contract.md). Chưa tính performance test. Tiếp theo mục5.

Audit lại mục4 đã phát hiện/sửa full-validation cohort guard,104/104 tests đạt. Kiểm độc lập raw actual/baseline/math/stdev/coverage đạt, scores không đổi;4 cuối năm bị loại h5 đúng split policy, không bỏ sót target không giải thích. Notebook06 có14 cells/7 code cell lưu output. [Audit và phạm vi còn chưa đánh giá](TV6_Evaluation_Audit.md). Chưa chạy held-out test; tiếp theo vẫn mục5.


M?c5 ho?n th?nh local ng?y27/11/2026:106 ki?m tra (104regression+2context), test502/498 m?u,9models,31metrics/8aggregates; ??i chi?u raw snapshot v? aggregate ??c l?p ??t. Notebook06 c?16cells/8code cells v?i output th?t. Persistence th?ng c?c model; kh?ng tuning sau test. [B?o c?o m?c5](TV6_Item5_Test_Evaluation.md). Ti?p theo m?c6 ph?n t?ch l?i/gi?i h?n.

Ki?m tr?ng t?m persistence gap: ph?t hi?n bias ?m v? l?i t?ng khi origin v??t train max; kh?ng train/tune/forward m?i. Notebook06 th?m2cells (18cells/9executedcode). Ch?a nghi?m thu to?n b? m?c6. Xem TV6_Persistence_Gap_Diagnosis.md.
