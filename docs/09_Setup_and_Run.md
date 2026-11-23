# Hướng dẫn cài đặt và chạy

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
