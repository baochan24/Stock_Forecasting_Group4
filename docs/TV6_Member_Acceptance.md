# Biên bản kiểm tra gói web trên máy thành viên

Mục đích: cung cấp bằng chứng thật cho điều kiện “ít nhất một thành viên khác chạy được release” trong rule.md. Kiểm trên máy leader hoặc chỉ điền tên reviewer không thay thế việc này. Không cần train model.

## Người nhận thực hiện

1. Nhận ZIP runtime web và checksum đúng cặp từ leader. Không dùng riêng ZIP inference mục7. Kiểm SHA trước khi giải nén:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'DUONG_DAN_GOI_WEB.zip'
```

So với file `.zip.sha256` đi kèm. Giải nén vào thư mục mới, giữ cây đường dẫn. Không giải đè lên project đang sửa.

2. Làm theo [hướng dẫn cài đặt](TV6_Member_Setup_and_Run.md), tạo môi trường riêng và cài lock. Gọi interpreter môi trường đó, không copy `.venv` từ leader.

3. Từ gốc thư mục vừa giải nén, chạy lệnh sau. Thay `TenThanhVien` bằng tên người thực hiện; chọn tên output mới nếu đã chạy trước:

```powershell
.venv/tv6_demo/Scripts/python.exe -m pip check
.venv/tv6_demo/Scripts/python.exe scripts/verify_tv6_web_handoff.py --http --reviewer "TenThanhVien" --output logs/member_acceptance_01.json
```

Verifier kiểm hash toàn bộ payload, release/sidecar, dự báo H1/H5, metric, trace và frontend/proxy HTTP bằng server tạm. Nó dùng đúng interpreter đang gọi và tự dừng server do nó tạo. Biên bản có môi trường, package versions, thời gian, số đầu ra và release SHA. Nếu lỗi, JSON có `passed: false` và thông báo lỗi. Không sửa JSON hoặc hash để chuyển lỗi thành đạt.

4. Chạy demo bằng hai terminal theo hướng dẫn. Chụp màn Dự báo một phiên và năm phiên; kiểm CNN chỉ có ở một phiên, số dòng lần lượt3/10 khi chọn đủ phương pháp. Kiểm So sánh mô hình và trace verified.

5. Gửi lại leader các thông tin sau qua kênh nhóm đã thống nhất; script không tự gửi hoặc upload:

| Nội dung | Người nhận ghi kết quả thực tế |
|---|---|
| Người thực hiện | Tên/thành viên |
| Máy thực hiện | Xác nhận máy của người nhận, không phải máy leader |
| Gói đã nhận | Tên ZIP và SHA-256 |
| Python/Windows | Theo biên bản và máy đang dùng |
| Cài mới từ lock | Có/không; gửi log lỗi nếu chưa đạt |
| `pip check` | Kết quả nguyên bản |
| Verifier | Gửi `logs/member_acceptance_01.json` nguyên bản |
| Demo | Ảnh H1/H5 và lỗi nếu có |
| Ngày kiểm tra | Ngày thực hiện thật |

Không gửi secrets, `.venv`, toàn bộ data hoặc checkpoint kèm biên bản. JSON có thể chứa đường dẫn local; kiểm thông tin cá nhân trước khi đưa vào báo cáo công khai, không thay các kết quả kiểm thử.

## Leader nghiệm thu

Đối chiếu ZIP SHA,release SHA và người thực hiện; xác nhận thao tác đã diễn ra trên máy khác. `reviewer_supplied` chỉ là thông tin người chạy khai báo. Verifier giữ `verified_on_other_machine: false` vì nó không thể tự xác minh danh tính và nơi chạy; leader ghi xác nhận riêng khi có bằng chứng.

Giữ biên bản gốc và ghi ngày/kết luận vào báo cáo bàn giao. Có lỗi thì giữ trạng thái chưa đạt và xử lý nguyên nhân, không sửa snapshot/model hoặc đánh dấu đã đạt thay người nhận.

## Kiểm browser tự động tùy chọn

Chỉ cần nếu máy có Node22+ và Chrome/Edge. Trong gói có checker mới, chỉ định Python và browser của máy người nhận:

```powershell
node scripts/check_tv6_frontend.mjs --python ".venv/tv6_demo/Scripts/python.exe" --browser "C:/Program Files/Google/Chrome/Application/chrome.exe"
```

Có thể thay bằng đường dẫn Edge. Checker không tải browser và không yêu cầu npm install. Nó chạy API/frontend riêng, lưu ảnh/checks trong `logs/audit/tv6_item9_*`. Kiểm thủ công vẫn cần để xác nhận người nhận sử dụng được demo.
