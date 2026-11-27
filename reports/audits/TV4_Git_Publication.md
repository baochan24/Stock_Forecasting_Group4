# Công bố phần TV4 trên nhánh TV4

Ngày 26/11/2026. Chuẩn bị từ commit 16555929210314b1eb06da9dc84b827ececc1b9e của nhánh TV4 bằng checkout riêng. Workspace làm việc và các file staged ngoài phạm vi được giữ tại nơi đang có.

Đã tích hợp source TV4 hoàn thành mục 1–10, tests, lock môi trường, docs, báo cáo và notebook có output. Các module TV1/TV2/TV3 mà training/factory phụ thuộc được đưa kèm từ source đã kiểm trong workspace, gồm validation, preprocessing, scaler/prepared/checkpoint và hai LSTM CPU float64.

Đã loại backend/experiments/management/experiment_runner.py cũ. Runner duy nhất ở backend/experiments/runner/experiment_runner.py. Nhánh chỉ công bố notebooks/04_TV4_Training_and_Experiments.ipynb, bản UPDATED phục vụ khôi phục editor được giữ ở workspace.

Cấu hình đã chốt cho các run được đặt trong experiments/configs/tv4_official. Chạy training sau khi nhận artifacts bằng --plan-dir experiments/configs/tv4_official. Không đưa dataset, scaler/checkpoint binary, logs sinh ra, ZIP, venv hoặc checkout lồng vào commit. Các artifacts thuộc gói bàn giao local được mô tả trong docs/TV4_Handoff_TV5_TV6.md.

Kiểm thử trực tiếp trên checkout chuẩn bị commit đạt 69/69, không skip, môi trường sạch và source imports đúng checkout. Receipt local tại logs/audit/tv4_tests_20261126T025608783185Z/summary.json trong checkout publication. Các số liệu 12 run, 1.075 epoch và model selection lấy từ báo cáo training đã kiểm chứng. Việc nhận và xác minh ở máy thành viên khác còn chờ kết quả thực tế.
