# TV1 — hạng mục 7: khám phá dữ liệu

## Phạm vi và bằng chứng

Đã chạy notebook theo flow mục 6 → mục 7 trên version `aapl_2015_2025_acq_20261119T141302002415Z`. Run EDA `20261119T153124185728Z`; không lỗi cell. Không tải mới, sửa snapshot, fit scaler, windowing hay train. Thống kê toàn kỳ là mô tả, không dùng test 2024–2025 để chọn model/seed/hyperparameter.

Raw hash `cbcadbc002d05bc27a573114b9bb73b930733585b7823d147ca3477354479351`, validated hash `ee56f9c782ac9e938985c680a9015d1ae198982e7d1cddc49ee5d67630c7b16d` giữ nguyên.

## Đặc điểm quan sát được

| Thống kê | Kết quả |
|---|---:|
| Giá theo phiên | 2.766 |
| Return một phiên | 2.765 |
| Giá thấp nhất / cao nhất | 20,53 / 285,20 USD |
| Median giá toàn kỳ | 88,16 USD |
| Mean / std giá toàn kỳ | 105,96 / 74,06 USD |
| Median giá năm 2015 / 2025 | 26,89 / 228,86 USD |
| Return phân vị 1% / 99% | -4,81% / +4,94% |
| Std return toàn kỳ, chưa annualize | 1,82%/phiên |
| Số phiên có absolute return >5% / >10% | 52 / 5 |

Giá thay đổi mức rõ rệt theo năm, vì vậy phân bố gộp không đại diện cho mọi giai đoạn. Năm 2020 có std return lớn nhất trong bảng mô tả theo năm. Không suy ra tính dừng, nguyên nhân thị trường hoặc chất lượng dự báo từ các quan sát này. Return đầu năm vẫn dùng phiên giao dịch trước đó; chỉ phiên đầu toàn snapshot không có return. Không tự điền giá để tạo return đầu tiên.

## Bảng và hình

Notebook có 5 hình: giá Close/Adj Close, volume, return và rolling std 30 phiên (hai panel), histogram return, boxplot giá và std return theo năm (hai panel). Tất cả export PNG 150 dpi vào `reports/figures/` với dataset version/run ID; đã kiểm tra hình phân bố năm không bị cắt nhãn.

CSV và JSON tại `data/metadata/eda/aapl_2015_2025_acq_20261119T141302002415Z/20261119T153124185728Z/`:

- `annual_statistics.csv`: count, min/median/max/mean/std giá, count/std return theo năm.
- `return_description.csv`: phân vị và mô tả return (%).
- `flagged_moves.csv`: 5 quan sát gắn cờ.
- `exploration_summary.json`: thống kê, danh sách hình và hash snapshot.

Mốc 30 phiên của rolling std chỉ để trình bày; ngưỡng 10% chỉ để điều tra. Không xóa quan sát boxplot hoặc phiên return lớn. Volume chỉ là ngữ cảnh, chưa phải feature bổ sung. Giá Yahoo điều chỉnh hồi cứu không phải point-in-time; lịch NASDAQ alias XNYS của thư viện giữ giới hạn đã ghi ở mục 5.

Hạng mục 7 hoàn thành ở mức mô tả và xuất bằng chứng. Hạng mục 8 tiếp tục đối chiếu nguồn cho từng biến động lớn; chưa gán nguyên nhân trong EDA.

## Bàn giao Drive

[Gói EDA đầy đủ](https://drive.google.com/file/d/1nQn96ROvOcpFJVkj4bptx9sWoejPQ_EG/view?usp=drivesdk) và [checksum](https://drive.google.com/file/d/1-GqZ-c3y7EzeZ0LcH6crt6Sv75HUUS8i/view?usp=drivesdk) đã upload vào Project_CW, đọc lại metadata xác nhận thư mục cha. Gói chứa 11 file: notebook có output, báo cáo, 5 PNG, 3 CSV, JSON summary; thêm manifest hash từng file. Kiểm tra CRC/hash nội dung gói đã đạt trước upload.

SHA-256 gói: `3bd4dbc4c5f7e90c4d52ca28b555eb03248ba7ade6fc3dd1db0c6ae9cb638b37`. Báo cáo trong ZIP là bản trước khi bổ sung link upload này; mọi số liệu và run ID giữ nguyên.
