# Decision log

## 22/11/2026 — TV2 đóng gói preprocessing và kiểm chứng sạch local

- Theo yêu cầu người dùng hoàn thiện mục cuối TV2: giữ contract1/5 bước, lưu prepared NPZ không pickle và JSON records riêng, manifest/source hashes; không đổi mô hình/phạm vi/shape.
- Ghim dependencies tại scripts/requirements-tv2-lock.txt; tạo venv TV2 sạch riêng, không sửa môi trường TV1. Package/verify source+TV1 artifacts+scaler+prepared, không upload/push.
- 51/51 tests đạt trong workspace và bản ZIP giải nén độc lập; rebuild arrays exact. Chi tiết evidence tại reports/audits/TV2_Final_Handoff.md. Nghiệm thu liên máy vẫn chờ người nhận xác nhận thực; không tự ghi hoàn thành thay họ.

## 21/11/2026 — đối chiếu trực tiếp hai tài liệu đề gốc

- Theo yêu cầu người dùng, đã đọc `docs/đề_yêu_cầu.md` và `docs/yêu_cầu_mẫu_đề_tài.md` sau khi lưu nội dung (trước đó cả hai rỗng).
- Xác nhận hướng Topic 4 regression/LSTM/Yahoo Finance/next-day và hai mở rộng multi-step, CNN vs. LSTM phù hợp thiết kế hiện tại; không thay phạm vi/contract/flow TV2.
- Cập nhật rule.md đưa hai nguồn vào danh sách đọc bắt buộc; bổ sung đối chiếu tại Project Description, tách yêu cầu đề gốc khỏi lựa chọn cụ thể của nhóm. Ghi còn mở về quyền sử dụng dữ liệu, phương án dự phòng và mốc kế hoạch; không tự công bố đã đáp ứng.
- Chỉ thay tài liệu, không chạy test thuật toán hoặc thay kết quả audit TV2. Tiến độ giữ ở mục 5 hoàn thành local, tiếp theo mục 6.

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

## 20/11/2026 — quy trình bám flow coursework tại workspace

- Người yêu cầu: người dùng trong phiên làm việc, yêu cầu setup rule.md để đọc cốt lõi trước code/quyết định, tránh lệch flow đồ án.
- Tạo `rule.md` tại gốc workspace, dựa trên Project Description, module boundaries, data contracts, phân công và quy tắc repo đã có; tạo `AGENTS.md` làm điểm chỉ dẫn coding agent đọc rule này.
- Ghi rõ tài liệu phải đọc, bất biến nghiên cứu, flow TV2 1–10, cách nghiệm thu và cập nhật local. Trạng thái chi tiết tiếp tục nằm trong báo cáo audit, không thay tài liệu thiết kế bằng log hội thoại.
- Không thay mục tiêu, mô hình, split hoặc contract; không tuyên bố đây là quyết định biểu quyết của toàn nhóm. Giữ nguyên rule của checkout lồng. Đây là thay đổi tài liệu, không chạy test thuật toán.

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
