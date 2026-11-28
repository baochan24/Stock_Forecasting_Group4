# Front-end

TV6 mục 9: AAPL Forecast Lab, bám concept nền sáng/sidebar/biểu đồ trung tâm/thẻ mô hình/nhật ký. HTML/CSS và ES modules, không có dependency npm hoặc build step. Chỉ gọi API, không train/fit scaler/tính MAE/RMSE riêng.

Từ gốc workspace, hai terminal:

```powershell
.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_api.py
.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_frontend.py
```

Mở **http://127.0.0.1:5173**. Chạy hai lệnh ở hai terminal riêng; nếu backend đã chạy thì chỉ cần lệnh frontend. Không mở index.html qua file://. Proxy chỉ chuyển tiếp `/api/v1/` về localhost:8000; đổi port bằng `--port`/`--api-port`. Không cache source, không expose workspace/artifacts qua static server. Dừng từng server bằng Ctrl+C.

- Dự báo: chọn ngày hợp lệ, horizon 1/5, seed cố định 42/123/456, các phương pháp; 5 phiên tự bỏ CNN. Actual đối chiếu nằm riêng; CSV tải từ kết quả đang hiển thị, không tính lại metric.
- Dữ liệu: snapshot, adjusted close, bảng/biểu đồ phân trang.
- So sánh: metric toàn tập release hoặc khoảng ngày gốc; dùng horizon/method/seed ở màn Dự báo. Đây là từng seed, không phải mean ba seed. Lịch sử train và audit đọc từ API, không train mới.
- Phân tích lỗi: error do backend trả, 100 dòng/trang; sắp |error| trong trang, không quảng cáo là top toàn tập.
- Nhật ký: tối đa 20 request thành công trong bộ nhớ tab; tải lại sẽ mất. Ngày chạy local khác ngày gốc lịch sử.
- Khám phá LSTM: gate trace được backend đối chiếu với PyTorch; hiển thị trung bình hidden, không diễn giải kinh tế.

Các thư mục con giữ ranh giới thiết kế. `api_client/client.js` sở hữu HTTP/error/timeout; `forecast_selection/state.js` sở hữu request/ghép comparison/CSV; `prediction_results/charts.js` sở hữu SVG/table đã escape; `app.js` điều phối màn hình.

Kiểm tra: `node --test tests/frontend/test_ui_contract.mjs`; kiểm thử browser/API thật: `node scripts/check_tv6_frontend.mjs` (Node22+, Chrome cài sẵn trên Windows). Script khởi chạy server/Chrome riêng, lưu receipt/screenshots trong logs/audit/tv6_item9_* và tự dừng các process do nó tạo. Không tác động server người dùng. Chưa triển khai Internet hoặc kiểm máy khác; ZIP inference mục7 chưa chứa frontend/API.

Lượt hoàn thiện mục10 thêm `--python "đường/dẫn/python.exe" --browser "đường/dẫn/chrome.exe"` (hoặc Edge) và TV6_PYTHON/TV6_BROWSER. Đã kiểm bằng venv mới cài từ lock:14 checks/5 tests JS đạt. Xem docs/TV6_Member_Acceptance.md để nhận biên bản từ máy thành viên; không tự coi kiểm cùng máy là máy khác.
