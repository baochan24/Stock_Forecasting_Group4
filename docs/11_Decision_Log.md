# Decision log

## 23/11/2026 — dọn bản upload TV3 dư theo yêu cầu người dùng

Xóa 9 file trong ba package ở gốc nhánh Thiên: `lstm_one_step/`, `lstm_multi_step/`, `model_trace/`. Source hiện hành vẫn ở `backend/models/` và `backend/model_trace/`; không đổi interface/float64/phạm vi mô hình. Đã kiểm tra imports và chạy lại 99/99 tests sau khi xóa. Giữ lịch sử Git, các module phụ thuộc và khung TV4–TV6. Chi tiết: `reports/audits/TV3_Branch_Cleanup.md`.

## 23/11/2026 — TV3 mục6 chuẩn bị/verify bàn giao

- Theo yêu cầu người dùng tiếp tục mục cuối và lưu báo cáo/notebook: chốt docs consumer TV4/TV6 và checkpoint persistence contract, không triển khai training/selection/API thay thành viên. Giữ CPU float64; diagnostic trained=False bị từ chối mặc định, không gắn nhãn model khởi tạo là model nghiên cứu.
- Source/contract ZIP có checksum, trained_checkpoints=[];99/99 tests, integration5460 samples và trace6 stages đạt sau giải nén bằng venv sạch. Notebook mục6 gọi kiểm manifest/checksum/receipt đúng gói; source cells hash độc lập outputs để Run All không làm sai integrity.
- Báo cáo TV3_Final_Handoff.md/TV3_Progress.md ghi gói cuối/evidence/giới hạn. Chỉ đạt kỹ thuật local, máy người nhận/checkpoint train thật/API approval còn chờ; không upload/push/merge hoặc tự nhắn thành viên khác.

## 23/11/2026 — TV3 mục5 môi trường CPU sạch và notebook

- Người dùng yêu cầu tiếp tục mục kế và luôn ghi báo cáo. Tạo lock68 dependencies, tv3_clean không system/user packages; không thay mô hình/dtype/split hoặc venv TV1/TV2.
- Strict runner89/89 đạt, pip-check/versions/origins/CPU build đạt; bản source độc lập chạy tests/integration5460 samples/trace6 stages đạt, hashes nguyên. Notebook03 cập nhật mục5 và chạy12/12 code bằng kernel sạch, đã đăng ký kernel VS Code riêng.
- Báo cáo tiến độ và evidence tại TV3_Progress.md/TV3_Environment_Reproduce.md, setup docs/TV3_Setup_and_Reproduce.md. Chỉ nghiệm thu local, máy khác vẫn chờ; mục6 bàn giao chưa làm. Không train/tuning/metric/push/merge/Drive.

## 23/11/2026 — TV3 mục4 trace và notebook

- Theo yêu cầu tiếp tục mục kế và luôn cập nhật notebook, nghiệm thu trace sau update/reload/JSON cho hai mode. Tăng độ chặt float64 rtol1e-10/atol1e-12 phù hợp precision64 đã chọn; fallback32 giữ1e-5/1e-6. Không thay core fields/API hoặc công thức, docs/TV3_Trace_Contract.md vẫn là schema nội bộ chưa được TV6 duyệt.
- 89/89 tests và6 stage checks input TV2 thật đạt; update synthetic không training AAPL. Bổ sung mục4 notebook03, cells gọi CLI/source thực và trình bày gates/recurrence/sai số;4 đạt local,5/6 chờ. Evidence tại TV3_Progress.md. Không push/merge/Drive hoặc thay artifacts cũ.

## 23/11/2026 — notebook ghi quá trình từng phần TV

- Người dùng yêu cầu mỗi phần có notebook/cells để tìm hiểu, kiểm định và trình bày giảng viên. Tạo notebook TV2/TV3 đúng notebooks/, giữ EDA TV1; TV3 chỉ ghi nghiệm thu đến mục3,4–6 chờ. TV4–TV6 thêm khi bắt đầu.
- Builder/execute trong scripts, notebook gọi source/tests thật và lưu outputs/evidence; không tạo pipeline song song, không train hoặc thay đổi artifacts đã chốt. Thêm notebook tools vào venv TV3 riêng, không sửa TV1/tv2_clean; chưa coi là nghiệm thu môi trường sạch.
- Bổ sung vào rule yêu cầu cập nhật đúng notebook sau mỗi mục; không tự upload/push hoặc thay ZIP TV2 cũ. Chi tiết thao tác tại notebooks/README.md.

## 23/11/2026 — TV3 mục3 nghiệm thu model float64

- Theo yêu cầu tiếp tục mục3, bổ sung11 acceptance tests, không đổi model/adapter/contract. Suite77/77 đạt; nghiệm thu kiến trúc/forward/state/gradient/weight update và lưu/nạp sau một bước Adam tổng hợp. Gradcheck dùng tiny shared forward, tests default model riêng; không chứng nhận hội tụ/accuracy/training loop.
- Evidence và giới hạn tại reports/audits/TV3_Progress.md mục3. Giữ dtype64 theo lựa chọn người dùng, không tạo checkpoint nghiên cứu hoặc metric từ test; chưa push/merge/Drive. Tiếp theo mục4 trace; môi trường sạch và bàn giao còn mục5/6.

## 23/11/2026 — người dùng chọn thử giữ float64 xuyên suốt TV3

- Người quyết định: người dùng đề nghị giữ float64 để tránh hạ precision, sau đó yêu cầu triển khai thử. Thay lựa chọn float32 adapter trước bằng float64 cho adapter/model, không đổi kiến trúc/shape/split/scaler. Torch LSTM/Linear khởi tạo dtype64 explicit, không set global default; tests và CLI đồng bộ. Dung sai copy=0, inverse giá float64 rtol=atol1e-12.
- 66/66 tests đạt,5460 mẫu thật đạt; không sửa TV2 artifacts hoặc tính metric dự báo. Benchmark synthetic CPU batch32 1thread đo Adam step64 gần3 lần32, numeric weights/input storage gấp2; không suy rằng64 dự báo tốt hơn. Logs và số đo tại TV3_Progress.md phần precision. Trace/state_dict64 đạt.
- Giữ float64 làm cấu hình local hiện tại theo lựa chọn người dùng; TV4 phải ghi dtype trong training/checkpoint configuration. Chưa có checkpoint chính thức cần migrate, chưa train/tuning/test-selection/push/merge. Các mục3–6 không tự coi hoàn thành.

## 23/11/2026 — TV3 mục2, ranh giới tensor TV2→model

- Theo yêu cầu người dùng, thêm adapter trong preparation chuyển batch TV2 float64 sang CPU float32 đúng dtype model hiện có, không đổi artifact/shape/feature hoặc kiến trúc. Chọn dung sai kiểm cast standardized rtol1e-6/atol1e-7 và kiểm rawUSD sau cast rtol1e-6/atol1e-4; không thay tolerance float64 của TV2.
- Thay fixture preprocessing PR cũ bằng output module TV2;63/63 tests và toàn bộ5460 mẫu thật forward đạt, evidence tại TV3_Progress.md. Không training/metric/chọn model bằng test, không refit/scaler hoặc push/merge. Môi trường sạch còn mục5; bước tiếp theo mục3.

## 23/11/2026 — tiếp nhận TV3 mục 1 đúng module

- Người dùng yêu cầu bắt đầu xử lý hạng mục đầu tiên TV3 sau audit. Tiếp nhận10 file Python nguyên nội dung từ nhánh Thiện commit1f209b70c5690fb5e41b3b26d8eab36b2b6c029d vào backend/models, backend/model_trace và tests/models đúng contract. Không move/delete file sẵn có hoặc sửa remote; không đổi Define/Design.
- Chạy workspace thực55/55 tests đạt, logs và giới hạn môi trường tại reports/audits/TV3_Progress.md. Chỉ nghiệm thu mục1; tích hợp TV2, model/trace acceptance và bàn giao còn theo flow mục2–6. Chưa training/push/merge/Drive.

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
