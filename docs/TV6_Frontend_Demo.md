# TV6 mục 9 — AAPL Forecast Lab

Giao diện phục vụ giải thích và kiểm chứng bài toán: 30 phiên adjusted close AAPL vào LSTM, dự báo 1 hoặc 5 phiên, so với persistence và CNN một bước. Bám ảnh `reports/figures/ui_concepts/TV6_AAPL_Forecast_Lab_Concept_v1.png` và nguyên tắc trong Decision Log 26/11/2026. Số liệu trong ảnh concept được thay bằng response API thực.

## Chạy demo

Từ gốc workspace, backend đang chạy ở 8000 thì giữ nguyên. Mở terminal thứ hai:

```powershell
.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_frontend.py
```

Mở http://127.0.0.1:5173. Nếu backend chưa chạy, dùng `.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_api.py` ở terminal riêng. Môi trường dùng API lock hiện có; frontend không cài npm. Node22+ và Chrome chỉ cần cho kiểm thử tự động.

## Kịch bản trình bày giảng viên

1. Màn Dữ liệu: chỉ nguồn Yahoo Finance, dataset version, phạm vi snapshot, adjusted close hồi cứu; phân biệt với live hoặc point-in-time.
2. Màn Dự báo: chọn 2025-06-16, một phiên, seed42 và ba phương pháp. Chạy inference; quan sát 30 input, T+1, giá thực tế và error; tải CSV nếu cần. Thẻ giá đầu là giá adjusted close ngày gốc, không phải giá thị trường hiện tại.
3. Chuyển năm phiên: CNN bị bỏ/disable, kết quả cũ bị xóa. Chạy lại, có đúng T+1..T+5 và 10 dòng cho LSTM/persistence. Ngày target do backend trả theo phiên dataset.
4. So sánh: đọc metric toàn tập test, đủ sample_count/error_count và từng horizon/overall. Chuyển khoảng ngày gốc và đọc lại để thấy scope khác nhau. Không chọn seed theo test; giá trị mặc định42 có từ trước. Không tính MAE/RMSE trong frontend.
5. Chọn run và xem history/config/audit. Loss scaled của hai biểu diễn khác nhau không so trực tiếp; dùng metric USD ở trên.
6. Phân tích lỗi: đọc stored results, ghi rõ trang và range. Sắp lỗi trong trang không phải chọn top lỗi toàn dataset.
7. Khám phá LSTM: trace summary thật, verified với nn.LSTM, 30 bước cổng trung bình hidden. Không gọi đây là giải thích nguyên nhân kinh tế.
8. Nhật ký: các lần inference thành công trong tab hiện tại. Chỉ là bộ nhớ phiên, không phải kho lưu lâu dài hoặc bằng chứng dự báo được phát hành trong quá khứ.

## Trạng thái và giới hạn

Loading/error/empty và stale response được xử lý: đổi context xóa kết quả cũ, request trả về sai context không ghi vào màn hình; nhật ký vẫn lưu request đã hoàn tất. Lỗi backend không thay bằng số liệu giả. API timeout90 giây; proxy localhost95 giây.

Frontend đọc release `aapl-research-residual-v1`, không thay model/scaler/split hoặc train. Residual đã phát triển sau khi xem test cũ: kết quả không phải holdout độc lập và demo không nâng bằng chứng chất lượng dự báo. Chưa live, trading, đăng nhập, deployment Internet hoặc kiểm tải/máy khác. Bàn giao trọn bộ thuộc mục10, ZIP inference mục7 không tự bao gồm API/sidecar/frontend.
