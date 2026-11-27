# Hướng dẫn cài đặt và chạy

**Máy thành viên mới:** xem [Hướng dẫn cài đặt và chạy AAPL Forecast Lab](TV6_Member_Setup_and_Run.md) để nhận đủ artifacts, tạo môi trường riêng, cài dependencies, kiểm release và chạy API/frontend. Chưa nghiệm thu máy khác; không cần train lại hoặc Docker.

## TV6 frontend — mục9 local

Giữ API đang chạy trên8000. Terminal riêng: `.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_frontend.py`; mở http://127.0.0.1:5173. Không cần npm install/build. [Kịch bản demo](TV6_Frontend_Demo.md), [nghiệm thu](../reports/audits/TV6_Item9_Frontend.md). 5 tests JavaScript/14 checks Chrome/API thật đạt. Notebook52cells/26code cells. Chưa deployment/máy khác; bên dưới là lịch sử từng giai đoạn.

## TV6 API — đã nghiệm thu local mục8

Xem [API setup và contract](TV6_API_Setup_and_Contract.md). Dependencies scripts/requirements-tv6-api-lock.txt, sidecarscripts/build_tv6_api_data.py, chạy scripts/run_tv6_api.py trên127.0.0.1:8000/docs.46tests/15HTTPchecks đạt; servertestđãdừng. Khôngtrain/newweights/frontend, chưa nghiệmthumáykhác.

## TV6 release inference — đã nghiệm thu local mục7

Xem [TV6 Release Contract](TV6_Release_Contract.md): ZIP cục bộ aapl-research-residual-v1, Python3.13.7/lockTV4, `python scripts/verify_tv6_release.py`. Không cầntrain hoặcdownloadYahoo. Đã kiểm nguồn giải nén riêng trêncùngmáy/dependencyenv; chưa xácnhậnmáy khác. API/frontend chưa triển khai; các nhận xét cũ bên dưới là lịch sử từngphần.

## TV2 preprocessing — hướng dẫn đã kiểm chứng local

Xem `docs/TV2_Setup_and_Handoff.md`: venv sạch Python3.13.7, scripts/requirements-tv2-lock.txt, runner tests, nạp prepared arrays/records và verify toàn gói giải nén. Kết quả cụ thể tại reports/audits/TV2_Final_Handoff.md. Không cần PyTorch/notebook/train để kiểm tra gói preprocessing; chưa chứng minh máy thành viên khác, chưa là hướng dẫn release model/web.

## Phần dữ liệu TV1

Hướng dẫn thực tế, đường dẫn Drive/artifacts, dependencies, kernel và lệnh tests/notebook: [TV1 Setup and Reproduce](TV1_Setup_and_Reproduce.md). Dataset hiện tại AAPL 2015–2025, không cần train lại để kiểm tra dữ liệu. Kết quả môi trường sạch cùng máy được ghi theo log thực thi, không thay xác nhận máy khác.

## Các phần hệ thống chưa triển khai/kiểm chứng

Các mục dưới chưa có lệnh chạy đã kiểm chứng; bổ sung khi triển khai phần tương ứng:
- Python/dependencies CPU đã xác minh.
- Cách nhận snapshot dữ liệu và release.
- Chạy pipeline nghiên cứu, inference, API và front-end.
- Kiểm tra health/readiness và lỗi thường gặp.
- Cách thành viên khác chạy mà không train lại.
Không ghi lệnh thành công hoặc phiên bản thư viện chưa được kiểm tra.
