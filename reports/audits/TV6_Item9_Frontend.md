# TV6 mục 9 — nghiệm thu AAPL Forecast Lab

Hoàn thành demo **local ngày 27/11/2026**, theo concept người dùng đã duyệt. Không train, refit scaler hoặc thay release/model.

## Kết quả

Nền sáng, sidebar, biểu đồ lịch sử/vùng dự báo, thẻ LSTM/CNN/persistence và nhật ký. Số liệu minh họa của ảnh concept được thay bằng API thật. HTML/CSS/ES modules không dependency npm; proxy chỉ bind localhost, không thư viện/font CDN.

- Dự báo: ngày hợp lệ,30 input,h1/h5,seed42/123/456. H5 tự bỏ CNN. Đổi context xóa kết quả cũ, bỏ response không còn khớp; lỗi không hiển thị dự báo cũ như kết quả mới. CSV đủ release/origin/target/method/horizon/prediction/actual/error, actual ghép sau inference.
- Data explorer: nguồn/version/phạm vi snapshot, adjusted close USD,100 dòng/trang.
- Comparison: MAE/RMSE backend cùng cohort, full-split hoặc khoảng ngày gốc; từng seed, sample/error count, horizon/overall và evaluation phase. Không tính metric trong trình duyệt.
- Experiment: configuration/checkpoint/audit/loss history. Nhãn loss scaled chỉ rõ không so trực tiếp residual/absolute.
- Errors: stored errors phân trang, đồ thị T+1, sắp |error| trong trang; không gọi top lỗi toàn tập.
- Journal:20 request thành công gần nhất trong bộ nhớ tab; thời gian chạy local/request ID khác ngày gốc lịch sử; reload sẽ mất.
- LSTM explorer: trace thật verified PyTorch, gate trung bình hidden32 trên30 bước, không diễn giải kinh tế.

## Bằng chứng

| Kiểm chứng | Kết quả |
|---|---|
| JavaScript contract/render/security helpers | 5 tests passed |
| Chrome headless, API/proxy thật | 14 checks passed |
| H1 / H5 | 3 / 10 dòng, CNN chỉ H1 |
| Full test H5 | 498 windows,overall2490 errors mỗi phương pháp |
| Selected range | Nhãn/bộ lọc riêng,12 dòng metric H5 |
| Trace | Verified true,30 bước |
| Responsive390px | Không tràn ngang trang, bảng/nav cuộn bên trong |
| Backend outage | Hiện lỗi, xóa dự báo cũ, export disabled |
| Browser | 0 uncaught exceptions |
| Release/sidecar | Hash hợp lệ, release SHA không đổi |
| Notebook | 52 cells/26 code cells,hai code cells mới có output thật |

Evidence cuối: `logs/audit/tv6_item9_20261127T091225920Z/` có summary/source hashes,checks,TAP,request bodies,6 screenshots,server/browser log,notebook verification và acceptance/hash các bằng chứng. Browser chỉ gửi release/origin/horizon/methods/seed, không target/raw input/checkpoint. Notebook replay request H5 qua backend thực, xác nhận10 dự báo; giữ output các mục trước. Lần thành công trước090747757Z giữ nguyên lịch sử; lần cuối kiểm lại sau sửa encoding chữ loading/error tiếng Việt.

Lệnh: `node --test tests/frontend/test_ui_contract.mjs`; `node scripts/check_tv6_frontend.mjs`. Checker dùng Chrome có sẵn/Node22 WebSocket/CDP, không cài browser package vào môi trường model; tạo/dừng server thử nghiệm riêng, không đụng backend người dùng8000.

QA đầu chưa đạt vì UI mở trước API startup (health503); đã sửa checker chờ backend health. Giữ evidence thất bại tại `logs/audit/tv6_item9_20261127T090553339Z/`. Node test đầu bị sandbox chặn spawn EPERM; chạy với quyền local phù hợp đạt5/5. Không tính hai lần này là kiểm tra đạt. Đã xem ảnh desktop/mobile đối chiếu concept; mobile chụp trạng thái đổi lựa chọn đã xóa kết quả cũ.

## Chạy và giới hạn

Giữ API8000, terminal riêng chạy `.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_frontend.py`, mở **http://127.0.0.1:5173**. Không npm install/build. Xem `docs/TV6_Frontend_Demo.md` và `frontend/README.md`.

Đủ nghiệm thu mục9 demo local. Chưa load test, deployment Internet/máy khác; ZIP inference mục7 chưa có API/sidecar/frontend, cần bàn giao mục10. Snapshot hồi cứu2015–2025, không live/trading. UI/API không biến test cũ sau phát triển residual thành holdout độc lập, không chứng minh LSTM thắng bền vững. Không commit/push/upload. Mục10 vẫn chờ.
