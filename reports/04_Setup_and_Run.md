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
