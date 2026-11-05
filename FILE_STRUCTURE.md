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
