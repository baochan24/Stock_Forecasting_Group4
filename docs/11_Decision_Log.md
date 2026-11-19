# Decision log

| ID | Quyết định | Trạng thái |
|---|---|---|
| D01 | AAPL adjusted close 2015–2025, CPU, PyTorch | Đã thống nhất |
| D02 | Train 2015–2022, validation 2023, test 2024–2025 | Đã thống nhất |
| D03 | LSTM direct price/persistence; CNN một bước lookback 30 | Đã thống nhất |
| D04 | LSTM direct multi-output 5, lookback 30, checkpoint riêng | Đã thống nhất |
| D05 | Web hoàn chỉnh; train riêng; release_id thay thuật ngữ demo toàn hệ thống | Đã thống nhất |
| D06 | Architecture/modules/data flow/API/risks/milestones | Đã thống nhất về thiết kế |
| D07 | LSTM học thay đổi giá | Tùy chọn sau phạm vi chính/mở rộng |

Thay đổi mới ghi: ngày, quyết định, lý do, ảnh hưởng, người quyết định và bằng chứng. Không tự ghi đạt khi chưa kiểm tra.

## 19/11/2026 — tiếp nhận TV1 và bố trí script EDA

- Theo yêu cầu người dùng trong phiên làm việc: lấy riêng source TV1 PR #5 vào workspace hiện tại để xử lý từng bước; chưa nghiệm thu và chưa merge/push GitHub.
- Nguồn: `huyenntt2110-crypto/Stock_Forecasting_Group4`, commit `08675d823bd2499df1508dc4b4cde8722d557629` (PR #5). Tiếp nhận downloader, validator, test và báo cáo dữ liệu; không lấy TV2.
- Chuyển hai script build/execute notebook từ `notebooks/` sang `scripts/` theo yêu cầu người dùng, phù hợp ranh giới entry point; cập nhật đường dẫn và `FILE_STRUCTURE.md`.
- Không thay đổi Define/Design hay hợp đồng dữ liệu. Snapshot EDA mới vẫn tách biệt snapshot TV1 chưa được bàn giao; các số liệu trong báo cáo TV1 là kết quả do tác giả báo cáo, chưa được xác nhận trên snapshot gốc ở workspace này.

## 19/11/2026 — TV1, tài liệu và tái lập

- Theo yêu cầu người dùng, hoàn thiện riêng TV1 và cập nhật notebook tại workspace trước khi upload bản sao Drive. Không merge/commit/push GitHub trong phiên này.
- Snapshot làm việc cố định `aapl_2015_2025_acq_20261119T141302002415Z`; gói raw và gói đầy đủ cùng các audit có hash/receipt riêng. Không nhận chúng là artifacts version cũ của tác giả PR.
- Ghim dependencies trực tiếp TV1 ở `notebooks/requirements-eda.txt`; hướng dẫn mới dùng venv sạch không kế thừa system/user site, thay cách cài phát triển ban đầu. Script execute nhận Python được chỉ định qua `TV1_NOTEBOOK_PYTHON` để kiểm chứng môi trường riêng, vẫn mặc định `.venv/eda` cho notebook hiện tại.
- Tái lập cục bộ trong workspace riêng ghi kết quả thực tế tại báo cáo hạng mục 10; chưa có xác nhận máy thành viên khác. Không đổi phạm vi AAPL/CPU/shape hay quy tắc thực nghiệm.

## 19/11/2026 — phát hành source TV1 lên nhánh Tâm

- Người dùng yêu cầu commit phần TV1 lên nhánh `Tâm` của `baochan24/Stock_Forecasting_Group4`. Commit nối tiếp head TV1 `08675d823bd2499df1508dc4b4cde8722d557629`; không merge vào main, không lấy TV2.
- Phạm vi: acquisition/validation, 34 tests, scripts dữ liệu, notebook có output, tài liệu/báo cáo TV1 và 6 hình có chủ đích. Dataset/scaler/checkpoint/ZIP/logs/venv và các bản sao PR audit không vào commit.
- Đã chạy lại 34 tests trong checkout riêng của nhánh trước commit. Workspace/staging ban đầu giữ nguyên. Báo cáo theo run ghi trạng thái trước khi phát hành được giữ làm lịch sử, không nhận là trạng thái Git hiện tại.
