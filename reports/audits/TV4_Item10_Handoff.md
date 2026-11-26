# TV4 mục 10 — nghiệm thu và bàn giao local

Ngày 26/11/2026. Source và artifacts đã được dựng thành bản sao khác thư mục, kiểm payload, nạp lại 12 model và chạy strict tests bằng môi trường TV4 sạch theo lock.

## Kết quả nghiệm thu

- 69/69 tests đạt, không fail/error/skip, imports đến source của bản sao.
- Verifier bản sao kiểm 430 file payload, 325 file inventory và nạp mới 12 checkpoint, validation MSE khớp metadata.
- Bộ model được chọn gồm 6 checkpoint lookback 30, mỗi horizon giữ cả ba seeds 42/123/456.
- Đã lưu source lịch sử đúng hash, cấu hình, tests, dữ liệu/scaler/prepared và logs.
- Hai notebook có đủ mục 1–10 với output, bảng kết quả và biểu đồ đã thực thi.

[Receipt nghiệm thu](../../logs/audit/tv4_item10_20261126T024452638782Z/summary.json)

## Sau 10 hạng mục thu được gì

| Phần | Đầu ra có thể sử dụng |
|---|---|
| Dữ liệu và model | Pipeline nhận artifacts TV2 đã kiểm chứng, CPU float64, LSTM một và năm bước |
| Huấn luyện | Adam/MSE, finite guards, weighted loss, validation, early stopping và best checkpoint |
| Thực nghiệm | 12 run, tổng 1.075 epoch, log loss/LR/thời gian, source/config hashes |
| Một bước | So lookback 10/30/60 cùng mẫu, chọn 30 theo mean validation MSE 0,003265939 |
| Năm bước | Ba seed, mean validation MSE tổng 0,007692942 và số liệu riêng 5 horizon |
| Kiểm chứng | Lưu/nạp thật, checksum, tests sạch, bản sao source và model chạy trên root khác |
| Trình bày | Notebook đầy đủ, biểu đồ loss và TensorBoard 12 run |
| Bàn giao | ZIP local có SHA256 và manifest payload, hướng dẫn TV5/TV6, verifier theo root |

## Phạm vi hoàn thành

TV4 hoàn thành thực thi và nghiệm thu local. Bản sao độc lập dùng cùng máy và môi trường TV4 sạch đã kiểm lock. Chưa có xác nhận ở máy người nhận, recipient_machine_verified=false. Gói được tạo local trong artifacts/releases và chưa gửi/upload.

Các model chọn bằng validation. Một số best ở giới hạn 100 epoch, cần giữ giới hạn hội tụ. Đánh giá test, MAE/RMSE USD, persistence/CNN và tích hợp thuộc phần việc tiếp theo của TV5/TV6. [Hướng dẫn consumer](../../docs/TV4_Handoff_TV5_TV6.md)
