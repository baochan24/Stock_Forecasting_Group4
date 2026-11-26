# File Structure

TV5 mục 3 dùng `backend/experiments/runner/cnn_data.py`, `scripts/check_tv5_aapl_data.py`, `tests/training/test_cnn_comparison_data.py` và notebook 05 để kiểm dữ liệu đối ứng LSTM.

TV5 mục 2 có `tests/models/test_cnn_contract.py` và `reports/audits/TV5_Item2_Architecture_Contract.md`. Source CNN khóa contract một bước và CPU float64. Notebook 05 giữ receipt tiếp nhận và kết quả tests hiện tại.

`reports/audits/TV5_Budget_Preliminary_20261126.md` ghi sơ khảo ngân sách trước mục 2, số đo TV4 và các phương án CNN chờ quyết định.

TV5 mục 1 tiếp nhận `backend/models/cnn_one_step/model.py`, `__init__.py` và `tests/models/test_cnn_one_step.py`. Notebook `notebooks/05_TV5_CNN_Development_and_Experiments.ipynb` dùng builder/executor chung với --member 5. Bằng chứng ở `reports/audits/TV5_Item1_Source_Intake.md`.

`reports/audits/TV5_PR9_Review_20261126.md` ghi audit nhánh TV5/PR #9 sau khi TV4 hoàn thành và flow 10 mục CNN cần thực hiện. `reports/audits/TV5_Progress.md` theo dõi tiến độ.

Mục 10 dùng `scripts/build_tv4_handoff.py` và `scripts/verify_tv4_handoff.py` để tạo/kiểm ZIP local trong artifacts/releases. `docs/TV4_Handoff_TV5_TV6.md` hướng dẫn consumer, `reports/audits/TV4_Item10_Handoff.md` tổng kết. Notebook đọc receipt tại logs/audit/tv4_item10_latest.json.

Sửa audit TV4 có `scripts/build_tv4_asset_inventory.py`, `scripts/verify_tv4_assets.py`, manifest `reports/audits/TV4_Run_Assets.json` và báo cáo `reports/audits/TV4_Audit_Fixes_20261126.md`. Snapshot backend lịch sử và entrypoint mục 8/9 nằm dưới `logs/audit/tv4_pre_fix_source_20261126/`.

`reports/audits/TV4_Items1_9_Review_20261126.md` ghi audit mục 1–9, kiểm chứng 12 checkpoint và các sai sót còn phải xử lý trước nghiệm thu cuối.

Mục 9 dùng tùy chọn `--five-step` của `scripts/train_tv4_one_step.py`, lưu YAML, logs, summary và hình ở `logs/audit/tv4_item9_<UTC>/`. Checkpoint năm bước có thư mục riêng tại `artifacts/checkpoints/tv4_item9_<UTC>/`. Exporter TensorBoard nhận `--summary` và `--output` để thêm lịch sử năm bước.

`scripts/export_tv4_tensorboard.py` xuất CSV mục 8 sang TensorBoard scalar events tại `logs/tensorboard/tv4_item8_20261125T122649342552Z/`. Môi trường dashboard riêng là `.venv/tv4_tensorboard`.

`notebooks/04_TV4_Training_and_Experiments_UPDATED.ipynb` là bản sao khôi phục đầy đủ 34 cell và output đến mục 8, tạo để mở qua đường dẫn mới khi tab notebook gốc bị giữ hoặc ghi lại bản cũ. File gốc cũng đã khôi phục cùng nội dung.

Mục 8 dùng `scripts/train_tv4_one_step.py` để chạy chín cấu hình lookback/seed theo kế hoạch mục 7. Mỗi đợt tạo thư mục `logs/audit/tv4_item8_<UTC>/` chứa YAML, run logs và summary. Checkpoints nằm trong `artifacts/checkpoints/tv4_item8_<UTC>/`. Notebook mục 8 đọc summary và lưu biểu đồ học.

TV4 item 7 uses scripts/prepare_tv4_experiment_plan.py to create immutable lookback artifacts, four YAML configs and integration evidence under logs/audit/tv4_item7_<UTC>/.


`reports/audits/TV4_Item7_Experiment_Plan.md` ghi audit trước thực nghiệm, đề xuất ngân sách và phụ thuộc pipeline lookback 10/60. Notebook TV4 mục 7 hiển thị báo cáo này.

TV4 mục 6 dùng `scripts/check_tv4_smoke.py`, lưu cấu hình, lịch sử run và summary vào `logs/audit/tv4_item6_<UTC>/`. Checkpoint hai horizon đặt trong `artifacts/checkpoints/tv4_item6_<UTC>/`.

TV4 mục 5 dùng tùy chọn `--checkpoint` của `scripts/check_tv4_training_run.py`. Checkpoint mỗi epoch cải thiện nằm dưới `artifacts/checkpoints/tv4_item5_<UTC>/`, gồm weights.pt và manifest.json theo contract TV3.

TV4 mục 4 dùng `scripts/check_tv4_training_run.py` cho phép thử AAPL trên 33 cửa sổ đầu mỗi tập. Kết quả nằm trong `logs/audit/tv4_item4_<UTC>/`, gồm biên bản và thư mục run chứa cấu hình, metadata và lịch sử epoch. `tests/training/test_tv4_run_acceptance.py` kiểm numerical guards, dừng sớm và log khi run lỗi hoặc bị ngắt.

`logs/audit/tv4_training_demo_<UTC>/` lưu bằng chứng minh họa của notebook 04 mục 3.1. Mỗi lần chạy sinh 3 hình PNG và các bảng `history.csv`, `train_batches.csv`, `validation_usd.csv` để đối chiếu hình với số liệu.

TV4 mục 3 dùng `backend/experiments/runner/aapl_factories.py` để tạo model và hai DataLoader, `scripts/check_tv4_aapl_data.py` để kiểm tra bằng dữ liệu thật và `tests/training/test_aapl_factories.py` để kiểm tra các cấu hình sai.

TV4 mục2: `tests/training/test_tv4_float64_contract.py` kiểm contract CPU float64 cùng LSTM TV3; `scripts/check_tv4_float64.py` tạo receipt probe tổng hợp và bảng notebook04. Source training thay đổi có chủ đích sau intake, source model/data/scaler TV1–TV3 giữ nguyên.

TV4 mục1 (25/11/2026):
- `backend/training/trainer.py`, `__init__.py`: source loop PR#10, cast float32/checkpoint hook còn chờ các mục sau.
- `backend/experiments/runner/experiment_runner.py`: vị trí runner đúng contract và imports.
- `backend/experiments/management/experiment_manager.py`: seed/run/config/log metadata.
- `experiments/configs/lstm_one_step_baseline.yaml`, `lstm_multi_step_baseline.yaml`: cấu hình mẫu tiếp nhận, chưa liên kết dataset thật.
- `tests/training/test_training_loop.py`, `test_experiment_runner.py`, `test_experiment_manager.py`: baseline tổng hợp.
- `scripts/run_tv4_checks.py`, `requirements-tv4-lock.txt`: runner evidence và pins môi trường riêng.
- `notebooks/04_TV4_Training_and_Experiments.ipynb`: quá trình TV4; builder/executor ở scripts hỗ trợ --member4.
- `docs/TV4_Setup_and_Reproduce.md`, `reports/audits/TV4_Progress.md`: hướng dẫn và tiến độ.

TV3 cleanup 23/11/2026: source LSTM/trace duy nhất dùng trong project nằm trong `backend/`; loại các bản upload dư ở ba thư mục gốc `lstm_one_step/`, `lstm_multi_step/`, `model_trace/` trên nhánh Thiên. Audit: `reports/audits/TV3_Branch_Cleanup.md`. Ghi nhận công bố Git: `reports/audits/TV3_Git_Publication.md`.

Đây là bộ khung có tài liệu trách nhiệm, chưa phải ứng dụng chạy được. Không thêm framework/API train/đăng nhập/giao dịch/cập nhật real-time ngoài phạm vi đã chốt.

## Thư mục cấp cao
| Thư mục | Vai trò |
|---|---|
| backend | Dữ liệu, models, training, evaluation, services và API |
| frontend | Vùng chức năng giao diện, framework còn mở |
| docs | Define/Design và hướng dẫn |
| reports | Bảy phần báo cáo và bằng chứng |
| data | Snapshot và dữ liệu chuẩn bị |
| experiments | Cấu hình và run |
| artifacts | Scaler, checkpoint và release |
| logs | Logs web/audit vận hành |
| tests | Vị trí kiểm tra theo trách nhiệm |
| scripts | Entry points triển khai sau |
| notebooks | Khảo sát và trình diễn, dùng logic chung |

## Danh sách file

### Bổ sung cục bộ ngày 19/11/2026

- `scripts/audit_tv1_completion.py` — audit lại artifacts/10 hạng mục và kết quả data, ghi report theo run ID.
- `reports/audits/TV1_Final_Audit.md` — bảng nghiệm thu cuối và findings đã xử lý/còn mở.


- `notebooks/requirements-tv1-lock.txt` — 65 phiên bản thư viện từ venv sạch đã chạy thành công; Windows/Python 3.13.

- `docs/TV1_Setup_and_Reproduce.md` — hướng dẫn nhận source/artifacts, môi trường/kernel và tái lập TV1.
- `scripts/check_tv1_reproducibility.py` — kiểm chứng trong workspace riêng bằng venv sạch trên cùng máy.
- `reports/audits/TV1_Reproducibility.md` — kết quả hạng mục 10 và giới hạn xác nhận độc lập.

- `scripts/run_tv1_checks.py` — chạy suite TV1, lưu summary/log/hash/môi trường theo run ID.
- `tests/data/test_handoff_integrity.py` — kiểm tra gói thật trên bản sao, thử các lỗi integrity.
- `tests/data/test_pipeline_integration.py` — pipeline offline tổng hợp, metadata/hash lỗi và bảo vệ output.
- `reports/audits/TV1_Test_Summary.md` — báo cáo hạng mục 9.

- `reports/audits/TV1_Anomaly_Sources.json` — ledger nguồn/bối cảnh/mức bằng chứng cho 5 phiên gắn cờ.
- `reports/audits/TV1_Anomaly_Review.md` — báo cáo điều tra mục 8, không sửa dữ liệu.

- `reports/audits/TV1_Data_Exploration.md` — kết quả EDA hạng mục 7, liên kết hình và bảng theo run ID.
- `reports/figures/<dataset_version>_<eda_run_id>_*.png` — 5 hình EDA thực, có ID riêng mỗi lần chạy.

- `backend/data/validation/standard_output.py` — nghiệm thu bảng chuẩn sau audit chất lượng.
- `tests/data/test_standard_output.py` — kiểm tra sai schema/hash/giá/ngày/định danh và audit cũ.
- `reports/audits/TV1_Standard_Output.md` — kết quả hạng mục 6.

- `tests/data/test_data_quality.py` — fixture kiểm tra ngày/giá/lịch phiên và OHLCV.
- `reports/audits/TV1_Data_Quality.md` — bằng chứng audit chất lượng snapshot, hạng mục 5.

- `scripts/verify_tv1_handoff.py` — xác minh ZIP đầy đủ, hash liên kết và raw/validated từng dòng; chỉ dùng thư viện chuẩn.

- `tests/data/test_snapshot_versioning.py` — kiểm tra version trùng, file dở, tranh chấp tạo file và lỗi tải.
- `reports/audits/TV1_Snapshot_Versioning.md` — bằng chứng bảo vệ snapshot hạng mục 4.

- `backend/data/validation/provenance.py` — kiểm tra nhất quán metadata với raw snapshot.
- `tests/data/test_provenance.py` — kiểm tra metadata thiếu/sai và raw bị thay đổi bằng fixture minh họa.
- `reports/audits/TV1_Metadata_Provenance.md` — phạm vi và kết quả hạng mục 3.

- `reports/audits/TV1_Snapshot_Handoff.md` — bằng chứng chuẩn bị bàn giao và trạng thái truy cập Drive.

- `scripts/package_tv1_snapshot.py` — đóng gói raw snapshot/metadata và kiểm tra hash trước bàn giao; không xuất bản.

- `.vscode/settings.json` — cấu hình IDE được người dùng yêu cầu để chọn môi trường EDA mặc định; không phải module sản phẩm.

- `reports/audits/TV1_Acquisition_20261119T141302002415Z.md` — bằng chứng lần thu thập AAPL mới bằng downloader TV1; chưa validation.

- `backend/data/acquisition/downloader.py` — lấy nguyên bản từ TV1 PR #5.
- `backend/data/validation/validator.py` — lấy nguyên bản từ TV1 PR #5.
- `tests/data/test_data_pipeline.py` — test nguyên bản TV1 PR #5.
- `reports/02_Data_Description.md` — cập nhật theo báo cáo TV1 PR #5; số liệu do TV1 báo cáo, chưa xác minh snapshot gốc trên máy này.
- `notebooks/01_AAPL_Data_Exploration.ipynb` — khám phá snapshot EDA mới, tách biệt artifacts TV1.
- `notebooks/requirements-eda.txt` — dependencies riêng của notebook.
- `scripts/build_data_exploration.py` — tạo notebook; chuyển từ `notebooks/` theo yêu cầu người dùng.
- `scripts/execute_data_exploration.py` — chạy notebook; chuyển từ `notebooks/` theo yêu cầu người dùng.
- `reports/audits/pr_review_2026_11_19/` — bằng chứng audit trước đó, bản sao PR và kết quả kiểm tra; không phải implementation chính.

Đây là tiếp nhận source cục bộ, chưa merge/commit/push GitHub. Chưa tiếp nhận phần TV2.

- `docs/12_Team_Assignment.md` — phân công model/train cho TV1–TV6; API/front-end do nhóm trưởng.

- `.gitignore`
- `README.md`
- `artifacts/checkpoints/README.md`
- `artifacts/releases/README.md`
- `artifacts/scalers/README.md`
- `backend/README.md`
- `backend/api/README.md`
- `backend/artifacts/README.md`
- `backend/audit/README.md`
- `backend/baselines/README.md`
- `backend/data/acquisition/README.md`
- `backend/data/preparation/README.md`
- `backend/data/transforms/README.md`
- `backend/data/validation/README.md`
- `backend/error_analysis/README.md`
- `backend/evaluation/README.md`
- `backend/experiments/management/README.md`
- `backend/experiments/runner/README.md`
- `backend/inference/README.md`
- `backend/model_trace/README.md`
- `backend/models/cnn_one_step/README.md`
- `backend/models/lstm_multi_step/README.md`
- `backend/models/lstm_one_step/README.md`
- `backend/services/results/README.md`
- `backend/training/README.md`
- `data/metadata/README.md`
- `data/prepared/README.md`
- `data/raw/README.md`
- `data/validated/README.md`
- `docs/01_Project_Description_and_Foundation.md`
- `docs/02_System_Architecture.md`
- `docs/03_Module_Boundaries.md`
- `docs/04_Data_Flow_and_Contracts.md`
- `docs/05_API_Contract.md`
- `docs/06_Technical_Risks.md`
- `docs/07_Milestones.md`
- `docs/08_Reproducibility_and_Release.md`
- `docs/09_Setup_and_Run.md`
- `docs/10_Open_Decisions.md`
- `docs/11_Decision_Log.md`
- `experiments/configs/README.md`
- `experiments/runs/README.md`
- `frontend/README.md`
- `frontend/api_client/README.md`
- `frontend/data_explorer/README.md`
- `frontend/error_analysis/README.md`
- `frontend/experiment_comparison/README.md`
- `frontend/experiment_details/README.md`
- `frontend/forecast_selection/README.md`
- `frontend/model_explorer/README.md`
- `frontend/prediction_results/README.md`
- `frontend/status_and_errors/README.md`
- `logs/audit/README.md`
- `logs/web/README.md`
- `notebooks/README.md`
- `reports/01_Problem_and_Scope.md`
- `reports/02_Data_Description.md`
- `reports/03_Implementation.md`
- `reports/04_Setup_and_Run.md`
- `reports/05_System_Demonstration.md`
- `reports/06_Baseline_and_Model_Comparison.md`
- `reports/07_Error_Analysis_and_Limitations.md`
- `reports/audits/README.md`
- `reports/figures/README.md`
- `reports/tables/README.md`
- `scripts/README.md`
- `tests/api/README.md`
- `tests/data/README.md`
- `tests/evaluation/README.md`
- `tests/integration/README.md`
- `tests/models/README.md`
- `tests/training/README.md`

`FILE_STRUCTURE.md` là tài liệu chỉ mục này. Không có model/data/results thật hoặc lệnh chạy đã xác minh trong ZIP.

## Bổ sung TV3 mục 1 — 23/11/2026

- `backend/artifacts/lstm_checkpoint.py`: persistence checkpoint contract, diagnostic/trained guards, strict CPU64 load.
- `tests/models/test_lstm_handoff.py`:10 tests tổng hợp về checkpoint handoff/corruption/identity/dtype/reuse.
- `scripts/package_tv3_handoff.py`, `verify_tv3_handoff.py`: gói source/contract và verify sau giải nén; không trained weights/upload.
- `docs/TV3_Handoff_TV4_TV6.md`: trách nhiệm/interfaces/checkpoint/inference/trace consumer và xác nhận nhận bàn giao.
- `reports/audits/TV3_Final_Handoff.md`: kết quả gói cuối/receipts/giới hạn và trạng thái chờ phối hợp.

- `scripts/requirements-tv3-lock.txt`:68 dependency versions cho môi trường Windows CPU/Python3.13.7, gồm notebook tools.
- `scripts/check_tv3_reproducibility.py`: source/artifacts copy độc lập + tests/integration/trace, bằng chứng local.
- `docs/TV3_Setup_and_Reproduce.md`: hướng dẫn tạo venv sạch/chạy tests/CLI/notebook và giới hạn liên máy.
- `reports/audits/TV3_Environment_Reproduce.md`: kết quả mục5, logs/commands/lock và phần còn chờ.

- `tests/models/test_lstm_trace_acceptance.py`: nghiệm thu trace sau update/reload/JSON, bất biến/mismatch/schema.
- `scripts/check_tv3_trace.py`: CLI kiểm2 representative inputs×3 stages, trace JSON có checksum.
- `docs/TV3_Trace_Contract.md`: schema trace nội bộ/conditions/tolerances/giới hạn, chưa là API web.

- `notebooks/02_TV2_Preprocessing_and_Audit.ipynb`: quá trình10 mục TV2 và outputs kiểm chứng.
- `notebooks/03_TV3_LSTM_Development_and_Tests.ipynb`: mục1–3 TV3, dtype và tests có outputs;4–6 ghi chờ.
- `scripts/build_member_notebooks.py`: builder theo TV2/TV3, bảo vệ overwrite và không nhân bản backend.
- `scripts/execute_member_notebooks.py`: kernel rõ ràng, chạy/lưu outputs và summary thực thi theo từng TV.

- `tests/models/test_lstm_acceptance.py`: mục3 nghiệm thu kiến trúc, numerical gradients, state/weights độc lập và disk state_dict roundtrip sau cập nhật tổng hợp.

- `scripts/benchmark_tv3_precision.py`: microbenchmark tổng hợp CPU1 thread float32/64 và kiểm state_dict/trace64; không đánh giá accuracy hoặc training chính thức.

Mục2 bổ sung:
- `backend/data/preparation/tensors.py`: adapter optional torch CPU float32 từ records/batch TV2, không fitting/training.
- `tests/models/conftest.py`: fixture nguồn TV2 tổng hợp.
- `tests/models/test_lstm_tv2_adapter.py`: tests consumer dtype/identity/no-target/copy/pairing.
- `scripts/check_tv3_tv2.py`: accept nguồn và kiểm adapter/forward trên cả hai bộ mẫu thật, giữ evidence.

- `backend/models/lstm_one_step/model.py`, `__init__.py`: LSTMOneStep và lõi LSTM nội bộ.
- `backend/models/lstm_multi_step/model.py`, `__init__.py`: LSTMMultiStep direct5.
- `backend/model_trace/lstm_trace.py`, `__init__.py`: trace tái dựng/đối chiếu.
- `tests/models/test_lstm_one_step.py`, `test_lstm_multi_step.py`, `test_lstm_contract.py`, `test_lstm_trace.py`:55 ca tests nền.
- `scripts/run_tv3_checks.py`: runner giữ logs/JUnit/summary/source hashes.
- `reports/audits/TV3_Progress.md`: trạng thái6 hạng mục và bằng chứng từng mục.
- `reports/audits/TV3_Thien_Branch_Audit_20261123.md`: audit nhánh gốc và giới hạn tích hợp.

## Bổ sung tiếp nhận TV2 — 2026-11-20

- `backend/artifacts/prepared.py`: persistence NPZ/JSON, source/scaler identity/checksums cho hai modes.
- `tests/data/test_tv2_prepared_artifacts.py`: roundtrip/corruption/version/path injection và chống ghi đè.
- `scripts/requirements-tv2-lock.txt`: 15 dependencies ghim cho Windows/Python3.13.7 sạch.
- `scripts/run_tv2_checks.py`: runner tests TV2, log/freeze/environment/source hashes.
- `scripts/package_tv2_handoff.py`: tạo prepared và ZIP source+artifacts có checksum, không upload.
- `scripts/verify_tv2_handoff.py`: xác minh gói giải nén, nạp/dựng lại hai modes không fit.
- `docs/TV2_Setup_and_Handoff.md`: setup/consumer/handoff/checklist xác nhận máy khác.
- `reports/audits/TV2_Final_Handoff.md`: kết quả đóng gói/repro local và giới hạn nghiệm thu.

- `backend/audit/tv2_leakage.py`: audit độc lập train moments và temporal coverage/exclusions.
- `tests/data/test_tv2_leakage_audit.py`: cố ý tạo scaler nhiễm tương lai, thiếu mẫu/ngày/exclusions sai để xác minh audit.
- `scripts/audit_tv2_leakage.py`: audit preprocessing hai mode trên snapshot/scaler thật và future-price perturbations.

- `backend/data/preparation/contracts.py`: kiểm tra input/target/batch và adapter chỉ nhận input.
- `tests/data/test_tv2_contracts.py`: hồi quy sai hợp đồng và không truyền target vào adapter.
- `scripts/check_tv2_contracts.py`: kiểm tra toàn bộ hợp đồng hai mode trên snapshot/scaler thật.

- `tests/data/test_tv2_five_step_windows.py`: kiểm tra direct 5-output, toàn bộ target cùng split và ranh giới/thiếu target.
- `windows.py` trong module preparation đã dùng chung lõi 1/5 bước; `scripts/check_tv2_one_step.py` hỗ trợ `--forecast-length 1/5` (giữ đường dẫn cũ).

- `backend/data/preparation/windows.py`: cửa sổ một bước lookback30, split theo target, nhận snapshot/scaler đã kiểm tra.
- `tests/data/test_tv2_one_step_windows.py`: đối chiếu cửa sổ, ranh giới, lịch sử/ID và kiểm tra tương lai không đổi input cũ.
- `scripts/check_tv2_one_step.py`: audit toàn bộ cửa sổ một bước trên snapshot thật.

- `scripts/check_tv2_scaling.py`: audit scaler lưu sẵn theo shapes/roundtrip/hash không đổi.
- `tests/data/test_tv2_saved_scaling.py`: shapes/formula/immutability/dtype/train hằng sau lưu/nạp.

- `rule.md`: quy trình đọc cốt lõi, bám flow coursework và nghiệm thu tại workspace.
- `AGENTS.md`: chỉ dẫn coding agent đọc rule.md trước triển khai/audit.

- `backend/data/preparation/preparation.py`: split_data và fit_scaler từ PR #2, chưa tích hợp pipeline.
- `backend/data/preparation/snapshot.py`: tiếp nhận snapshot TV1 read-only, kiểm tra hash/provenance/chất lượng.
- `scripts/inspect_tv2_input.py`: CLI kiểm tra snapshot cụ thể, lưu bằng chứng mới trong logs/audit.
- `scripts/inspect_tv2_split.py`: CLI audit gán split theo target và lịch sử trước ranh giới, không tạo windows.
- `backend/data/preparation/train_scaler.py`: chọn giá train từ snapshot đã kiểm tra và fit một lần.
- `backend/artifacts/scaler.py`: lưu/nạp JSON scaler và kiểm tra manifest/hash/phiên bản.
- `scripts/build_tv2_scaler.py`: tạo scaler mới và kiểm tra reload/roundtrip, ghi evidence.
- `tests/data/test_tv2_train_scaler.py`: train-only fit, reload không fit, snapshot mismatch và chống ghi đè.
- `tests/data/test_tv2_temporal_split.py`: kiểm tra ranh giới target, 5 target cùng split và bảo toàn lịch sử.
- `tests/data/test_tv2_snapshot.py`: kiểm tra nhận snapshot và từ chối artifacts sai bằng fixture tổng hợp.
- `backend/data/transforms/scaling.py`: scale/inverse_scale từ PR #3.
- `tests/data/test_tv2_imported_code.py`: kiểm tra scaler/roundtrip của phần tiếp nhận.
- `reports/audits/TV2_PR_Audit_20261120.md`: audit và checklist hoàn thiện TV2.
# TV5 mục 4

- `scripts/build_tv5_handoff.py` — ZIP/stage TV5 với dữ liệu và model dependencies, checksum từng file.
- `scripts/verify_tv5_handoff.py` — kiểm package ở root giải nén, 162 tests và tái tính so sánh/monitoring.
- `docs/TV5_Setup_and_Handoff.md` — môi trường, tái lập và consumer checkpoint.

- `backend/error_analysis/validation_monitoring.py` — monitoring lỗi validation, rolling20/top errors/monthly metrics.
- `tests/evaluation/test_validation_monitoring.py` — cửa sổ không dùng tương lai và từ chối predictions không đồng nhất.
- `scripts/build_tv5_monitoring.py` — artifacts monitoring và inventory telemetry.

- `backend/baselines/persistence.py` — baseline input-only giá USD cuối lịch sử.
- `backend/evaluation/one_step.py` — strict aligned one-step MAE/RMSE USD.
- `tests/evaluation/test_one_step_comparison.py` — tính tay metric/persistence và từ chối sai alignment.
- `scripts/compare_tv5_validation.py` — so sánh 3 CNN/3 LSTM/persistence trên validation chung, chưa đánh giá test.

- `backend/experiments/runner/cnn_plan.py` — chặn drift config chính thức phương án A.
- `experiments/configs/cnn_one_step_option_a.lock.json` — semantic config/fingerprint/ngân sách ba seed.
- `scripts/run_tv5_official.py` — ba run CNN, kiểm best/reload và thống kê validation.
- `tests/training/test_cnn_plan.py` — kiểm drift config và lock fingerprint sai.

- `scripts/run_tv5_smoke.py` — bounded AAPL CNN diagnostic 5 epoch, shared runner và kiểm reload best.

- `scripts/tv5_notebook_diagrams.py` — bốn sơ đồ dữ liệu, CNN shape, training và checkpoint cho notebook 05.

- `backend/artifacts/cnn_checkpoint.py` — immutable CNN weights/manifest, provenance và strict reload.
- `tests/training/test_cnn_checkpoint.py` — persistence CNN và tích hợp runner bằng fixtures tổng hợp.

- `scripts/audit_tv5_items_1_5.py` — audit source/config/protected hashes, hồi quy và forward dữ liệu thật trước mục 6.

- `backend/experiments/runner/cnn_factories.py` — factory CNN và adapter config cho loader chung.
- `experiments/configs/cnn_one_step_baseline.yaml` — phương án A, cùng data reference LSTM lookback30/common60.
- `tests/training/test_cnn_runner.py` — tích hợp CNN với trainer/runner TV4.

- `tests/models/test_cnn_learning.py` — diagnostic gradients, Adam, dropout và state_dict file thật.

