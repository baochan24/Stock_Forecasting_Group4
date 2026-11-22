# File Structure

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
