# Hoàn thiện phần còn lại của TV6 và bàn giao

Ngày28/11/2026, theo yêu cầu hoàn thiện công việc dang dở sau mục10. Không train/tune/refit hoặc thay dataset, scaler, checkpoint và kết luận hiệu năng. Release nghiên cứu vẫn là `aapl-research-residual-v1` với semantic SHA `a4b04a50c3e499b95407a5a8f9de379a40f6371bbb532cc01df90fdb2b5719a3`.

## Phần đã hoàn thiện thêm

| Công việc | Bằng chứng đã có |
|---|---|
| Cài mới từ lock | Tạo venv mới, không system-site-packages; pip install thành công,85 phiên bản khớp, pip check sạch |
| Xác minh import | torch/numpy/pandas/fastapi được import từ venv mới, không lấy từ môi trường TV4 cũ |
| Regression trên môi trường mới | 62 tests API/handoff đạt,0 lỗi/skip; hai warning deprecation giữ nguyên trong log |
| Browser/API thật trên môi trường mới | 14 checks Chrome và5 tests JavaScript đạt; lưu screenshots và request input-only |
| Verifier cho người nhận | Có `--http`, `--reviewer`, `--output`; JSON có môi trường/package/time/checks; không ghi đè biên bản cũ |
| Bảo vệ payload | 11 tests chống sửa/thiếu file, path/manifest sai và ghi đè biên bản đạt; gồm trong62 tests trên |
| Browser checker portable | Có `--python`/`--browser` hoặc TV6_PYTHON/TV6_BROWSER; không còn bắt buộc interpreter của leader |
| Bảng kết quả báo cáo | Có3 CSV tổng hợp/từng horizon/từng seed,59 dòng per-seed và provenance hash; không tính metric mới |
| Hướng dẫn nghiệm thu máy khác | Có quy trình và mẫu ghi nhận, người nhận gửi JSON/ảnh thật; script không tự gửi hoặc tự xác nhận máy khác |

Evidence cài mới nằm ở `logs/audit/tv6_closure_20261128T034730979767Z/`: fresh_install,environment_check,pip_check,fresh_tests và local_checks. Pointer hiện hành: `logs/audit/tv6_closure_latest.json`. Browser receipt được ghi trong local_checks và `logs/audit/tv6_item9_latest.json`.

Môi trường mới được cài từ wheel/cache của pip là cài đặt riêng thực sự; không phải sao chép site-packages. Nó vẫn nằm trên cùng máy và dùng cùng bản Python nền, nên không thay thế bằng chứng một thành viên khác chạy được release.

Lượt test payload đầu phát hiện đường dẫn `/absolute` trên Windows bị nhận diện ở kiểm tra containment muộn; đã bổ sung chặn rõ path bắt đầu `/`, rồi chạy lại11/11 và62/62. Giữ XML lượt lỗi để truy vết, không tính lượt đó là đạt.

## Gói runtime cuối và phạm vi

Builder tạo ZIP mới, không ghi đè ZIP/release cũ. Gói gồm source/runtime API/frontend,release artifacts vàsidecar đúng đường dẫn,các bảng CSV,docs,notebook saved outputs,verifier vàbrowser checker mới. Tên gói/checksum mới nhất ở `logs/audit/tv6_web_handoff_latest.json`. Kiểm nguồn giải nén vàHTTP bằng môi trường vừa cài được ghi riêng vào cùng folder closure sau bước đóng gói; đối chiếu archive SHA để biết chính xác gói nào đã được kiểm.

Các cờ verification trong manifest phản ánh thời điểm đóng gói; kết quả kiểm sau đó là biên bản bên ngoài gắn với SHA của ZIP. Không sửa manifest trong gói đã khóa để cập nhật trạng thái. Gói runtime không chứa toàn bộ research logs/prepared cho RunAll mọi notebook hoặc tái tạo training; notebook đã lưu output để đọc.

## Kết luận và điều kiện bên ngoài

Phần kỹ thuật chuẩn bị/cài mới/kiểm local/báo cáo và công cụ bàn giao đã có bằng chứng. Chưa thể tự ký ba điều kiện còn lại:

1. Một thành viên khác chạy trên máy của họ và gửi biên bản. Xem [hướng dẫn](../../docs/TV6_Member_Acceptance.md). Tên reviewer là khai báo, không tự chứng minh nơi chạy.
2. Quyền phân phối dataset hoặc nguồn thay thế được chấp thuận; xem [trạng thái dữ liệu](../../docs/TV6_Data_Use_and_Limits.md).
3. Định dạng/hạn nộp cuối được nhóm và giảng viên xác nhận. Không tự đặt deadline hoặc tạo xác nhận thay người khác.

Không upload/push/deploy trong lượt hoàn thiện này. LSTM residual vẫn chỉ nhỉnh nhẹ persistence trên test cũ sau phát triển, không phải bằng chứng vượt baseline độc lập/bền vững. Việc cài và demo chạy được không làm thay đổi kết luận khoa học đó.
