# TV4 mục 9 — LSTM năm bước

Hoàn tất training ngày 25/11/2026, hoàn thiện notebook và báo cáo ngày 26/11/2026. Ba run độc lập dùng seeds 42/123/456, lookback 30, 1.980 mẫu train và 246 mẫu validation. CPU float64, một luồng tính toán, LSTM một lớp hidden 32, Adam 0,001, batch 32, MSE tổng trung bình đều năm bước, max_epochs 100 và patience 10. Mỗi run khởi tạo mới và checkpoint riêng.

| Seed | Epoch kết thúc | Best epoch | Validation MSE tổng |
|---|---:|---:|---:|
| 42 | 100 | 100 | 0,007562351 |
| 123 | 100 | 100 | 0,007852059 |
| 456 | 100 | 100 | 0,007664417 |

MSE trung bình ba seed là 0,007692942, độ lệch chuẩn mẫu ddof=1 là 0,000146946. Các giá trị dùng giá chuẩn hóa. Cả ba run chạm ngân sách và có best ở epoch cuối, vì vậy chưa đủ cơ sở kết luận hội tụ hoàn toàn.

| Horizon | Validation MSE trung bình | Độ lệch chuẩn mẫu |
|---|---:|---:|
| 1 | 0,003761089 | 0,000242274 |
| 2 | 0,005625192 | 0,000702199 |
| 3 | 0,007337972 | 0,000203251 |
| 4 | 0,009453380 | 0,000844420 |
| 5 | 0,012287079 | 0,000503510 |

Trong đợt này sai số trung bình tăng theo khoảng dự báo. Mỗi checkpoint best được nạp vào model mới, kiểm lại MSE tổng và từng horizon với log ở best epoch, dung sai tương đối 1e-12. SHA256 mã nguồn, YAML và weights đều khớp. Tổng 300 epoch, thời gian trainer khoảng 355,733 giây. [Summary](../../logs/audit/tv4_item9_20261125T140320407544Z/summary.json) · [Biên bản kiểm chứng](../../logs/audit/tv4_item9_20261125T140320407544Z/verification.json)

Notebook gốc và UPDATED có mục 9, bảng từng seed và horizon, biểu đồ đường học cùng biểu đồ sai số từng bước. [Đường học](../../logs/audit/tv4_item9_20261125T140320407544Z/learning_curves.png) · [Sai số từng horizon](../../logs/audit/tv4_item9_20261125T140320407544Z/horizon_errors.png)

TensorBoard thêm ba run dưới nhóm five_step, mỗi run có loss, learning rate, thời gian và năm scalar horizon. Dữ liệu xuất từ CSV training đã hoàn tất. Đánh giá test, MAE/RMSE USD và so sánh baseline thuộc giai đoạn đánh giá sau. Bước tiếp theo theo flow TV4 là mục 10, audit cuối, tái lập và bàn giao.
