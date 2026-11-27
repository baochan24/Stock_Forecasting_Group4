# TV1 — hạng mục 8: điều tra các phiên biến động lớn

## Đầu vào và cách kiểm tra

Tiếp nối EDA mục 7 trên snapshot `aapl_2015_2025_acq_20261119T141302002415Z`. Review run `20261119T154140185489Z`. Quy tắc: tất cả 5 phiên có absolute return Adj Close >10%; không khẳng định đây là mọi anomaly có thể có. Đối chiếu giá phiên trước, return Close/Adj Close, thay đổi hệ số Adj Close/Close, OHLCV và cửa sổ ±2 phiên. Các cửa sổ có thể trùng phiên; không coi các dòng lặp là mẫu độc lập.

## Kết quả định lượng

| Ngày | Return Adj Close | Hướng xử lý |
|---|---:|---|
| 2020-03-13 | +11,9809% | Giữ nguyên |
| 2020-03-16 | -12,8647% | Giữ nguyên |
| 2020-03-24 | +10,0325% | Giữ nguyên |
| 2020-07-31 | +10,4689% | Giữ nguyên |
| 2025-04-09 | +15,3289% | Giữ nguyên |

Cả 5 phiên cũng vượt 10% ở Close; chênh lệch return giữa hai chuỗi nhỏ hơn 0,01 điểm phần trăm. Không thấy bằng chứng cú nhảy chỉ do thay đổi hệ số điều chỉnh. Đây là đối chiếu nội bộ cùng nguồn, không xác thực độc lập từng giá với sàn. Chất lượng OHLCV/ngày đã được kiểm tra ở mục 5.

## Bối cảnh có nguồn

- 13/03/2020: phục hồi thị trường cùng thông báo khẩn cấp COVID-19. [Reuters, 13/03](https://ng.investing.com/news/stock-market-news/global-marketslate-wall-street-rally-leads-global-stocks-higher-oil-also-jumps-153143).
- 16/03/2020: bán tháo thị trường trong lo ngại COVID-19. [Reuters, 16/03](https://ng.investing.com/news/stock-market-news/us-stockswall-st-sinks-as-virus-spread-escalates-worries-154288?ampMode=1).
- 24/03/2020: phục hồi trong kỳ vọng hỗ trợ tài khóa. [Standard Chartered, báo cáo 25/03 mô tả phiên 24/03](https://www.sc.com/en/uploads/sites/66/content/docs/pvb-market-watch-us-close-to-sealing-usd2tn-stimulus-25-march-2020.pdf).
- 31/07/2020: phiên sau kết quả kinh doanh và thông báo split. [Apple, 30/07](https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/) xác nhận giao dịch split-adjusted bắt đầu **31/08**, không phải 31/07; không chia lại giá thêm 4 lần. [Tin AAPL cùng phiên](https://www.fool.com/investing/2020/07/31/why-apple-stock-soared-to-a-new-all-time-high-toda.aspx).
- 09/04/2025: bối cảnh tạm hoãn nhiều thuế quan, ngoại trừ Trung Quốc. [Reuters / Kitco](https://www.kitco.com/news/off-the-wire/2025-04-09/stocks-spring-higher-dollar-gains-trump-announces-tariff-pause). [MacRumors](https://www.macrumors.com/2025/04/09/apple-stock-up-tariff-pause/) phản ánh AAPL trong phiên; mức tăng trong tin không thay return đóng cửa tính từ snapshot.

Các nguồn xác nhận bối cảnh/sự kiện, không chứng minh tác động nhân quả riêng của AAPL hoặc giải thích toàn bộ độ lớn return. Ledger `TV1_Anomaly_Sources.json` lưu publisher, ngày xuất bản, URL, mức bằng chứng và quyết định cho từng phiên; đã đọc/đối chiếu nguồn ngày 19/11/2026. Không chép nguyên văn bài báo. Không đưa tin tức hoặc phiên tương lai vào model.

## Kết luận và bằng chứng cục bộ

Đã điều tra 5/5 phiên gắn cờ; **giữ nguyên cả 5**, không xóa, winsorize, nội suy, đổi giá hay sửa split. Không có bằng chứng đủ để sửa dữ liệu; không tuyên bố chắc chắn mọi giá nguồn đều đúng. Có thể đối chiếu nhà cung cấp/sàn độc lập thêm nếu phát hiện mâu thuẫn sau này.

Notebook mục 8.1–8.3 đã được cập nhật trực tiếp và chạy thành công, không lỗi cell. Có bảng đối chiếu, cửa sổ giá, link nguồn và hình 5 panel. Bằng chứng tại `data/metadata/eda/aapl_2015_2025_acq_20261119T141302002415Z/20261119T154140185489Z/anomaly_review/`: `event_review.csv`, `event_windows.csv`, `anomaly_review.json`. Hình: `reports/figures/aapl_2015_2025_acq_20261119T141302002415Z_20261119T154140185489Z_anomaly_event_windows.png`.

Raw hash vẫn `cbcadbc002d05bc27a573114b9bb73b930733585b7823d147ca3477354479351`; validated hash vẫn `ee56f9c782ac9e938985c680a9015d1ae198982e7d1cddc49ee5d67630c7b16d`. Notebook kiểm tra lại hai hash sau review. Bước tiếp theo: mục 9 tổng hợp kiểm thử, rồi mục 10 tài liệu/tái lập. Chưa xác nhận người nhận độc lập ở mục 2.

## Bản sao Drive sau khi xác minh notebook cục bộ

Đã xác nhận mục 8 có trên file notebook ở workspace và không có cell lỗi trước khi đóng gói/upload. [Gói bằng chứng](https://drive.google.com/file/d/1F-johutLMzSQ2a8sybQPN0XHlEP50ck7/view?usp=drivesdk), [checksum](https://drive.google.com/file/d/1GkUe-VfgOsqJoSWl2C1-QdWCMagDPXrr/view?usp=drivesdk). Đọc lại metadata xác nhận đúng Project_CW. Gói gồm 7 file (notebook, ledger nguồn, báo cáo, hình, hai CSV và JSON), kèm manifest hash. SHA-256 ZIP `5d38e893a8f92a9b5f271ac4dc1dec70e7ba498e144f12cbcdd79ec901546384`. Báo cáo trong ZIP là bản trước phần link upload này; nội dung điều tra không đổi.
