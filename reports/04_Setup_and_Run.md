## Tổng kết hiện hành — audit mục10, 28/11/2026

Hướng dẫn máy thành viên: [TV6_Member_Setup_and_Run.md](../docs/TV6_Member_Setup_and_Run.md). Windows64/Python3.13.7 tham chiếu,tạo môi trường riêng,pip install theo scripts/requirements-tv6-api-lock.txt,pip check,verify release vàsidecar. Không cầnDocker/GPU/npm install hoặc train lại.

Runtime web cần đủ source+release artifacts+API sidecar/registry+frontend; chỉcloneGit hoặcZIP inference mục7 chưa đủ. Chạy scripts/run_tv6_api.py vàscripts/run_tv6_frontend.py ở2terminal,mở127.0.0.1:5173. Bàn giao mới cómanifest/checksum vàverifier riêng; chỉkết luận tái lập nguồn giải nén cùngmáy khi córeceipt,không gọi làmáy khác.

---

## Lịch sử các giai đoạn — không dùng làm trạng thái hiện tại

# Cài đặt và chạy

## TV6 API mục8

[API setup](../docs/TV6_API_Setup_and_Contract.md), [nghiệm thu](audits/TV6_Item8_API.md). API lịch sử chạy bằngscripts/run_tv6_api.py; cầnrelease mục7 vàsidecarAPI.46tests/15HTTPchecks thật đạt, khôngtrain. Frontendvàmục10 bàn giaocònchờ.

## Bổ sung TV6 mục7 — release inference không cần train

[Hợp đồng và cách chạy release](../docs/TV6_Release_Contract.md), [nghiệm thu](audits/TV6_Item7_Release_Integration.md). Gói aapl-research-residual-v1 nạp được từworkspace vàZIPgiảinén bằngPythonisolatedprocess; cùngmáy/dependencyenv. Dùngscripts/verify_tv6_release.py, khôngfit/train hoặc gọiYahoo. API/frontend còncác bước sau; trạngtháiTV1 bên dưới làlịch sử.

Trạng thái: đã có hướng dẫn phần dữ liệu TV1 tại [docs/TV1_Setup_and_Reproduce.md](../docs/TV1_Setup_and_Reproduce.md); chưa có lệnh model/training/API/web được nghiệm thu trong phần việc này.

## Nội dung cần hoàn thiện

TV1: nhận source hiện tại và đúng snapshot từ Drive, cài Python 3.13 cùng dependencies ghim, verify ZIP, chạy 34 tests và notebook. Cách chọn kernel/lỗi NumPy, vị trí artifacts và quy trình xác nhận người nhận đều ở hướng dẫn. Không tải lại Yahoo để thay bản đã bàn giao.

## Bằng chứng

Liên kết dataset version, run/release, logs, audit và phép kiểm tra liên quan khi có. Không điền số liệu giả hoặc kết luận trước thực nghiệm.

TV1 đã kiểm chứng trong venv sạch và workspace riêng trên cùng máy: pip check đạt, 33 tests đạt, notebook 19 code cell hoàn tất. Run `20261119T155705920238Z`; [báo cáo tái lập](audits/TV1_Reproducibility.md). Chưa xác nhận máy thành viên khác, chưa nghiệm thu model/API/web.
