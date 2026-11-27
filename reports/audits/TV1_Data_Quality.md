# TV1 — hạng mục 5: kiểm tra chất lượng dữ liệu

## Kết quả đã thực thi ngày 19/11/2026

Snapshot `aapl_2015_2025_acq_20261119T141302002415Z`: 2.766 dòng, 2015-01-02 đến 2025-12-31. Raw SHA-256 `cbcadbc002d05bc27a573114b9bb73b930733585b7823d147ca3477354479351`; metadata SHA-256 `71213959ec9c111a1826db9058dc41f61772af9a0324a4e32ff61eb3bf0edc24`.

| Kiểm tra | Kết quả |
|---|---:|
| Ngày không hợp lệ/sai định dạng | 0 |
| Ngày trùng | 0 |
| Giá thiếu/không phải số | 0 |
| Giá Inf/-Inf | 0 |
| Giá không dương | 0 |
| Phiên thiếu so lịch tham chiếu | 0 |
| Phiên ngoài lịch/phạm vi | 0 |
| Open/High/Low/Close/Volume lỗi | 0 |
| OHLC không nhất quán | 0 |
| Dòng bị xóa/điền | 0 |

Thứ tự thời gian tăng dần. Số phiên theo giai đoạn là 2.014 / 250 / 502; đây là số dòng trước windowing, không phải số mẫu model. Bảng chuẩn tạo trong bộ nhớ khớp từng giá/ngày với validated đã bàn giao trong dung sai 1e-12. Không ghi đè raw, metadata, validated hoặc validation report cũ.

## Lịch phiên và giới hạn

`exchange_calendars==4.13.3`, lịch yêu cầu `NASDAQ`, thực tế thư viện ánh xạ sang `XNYS`. Báo cáo ghi cả hai tên, phiên bản và danh sách thiếu/thừa. Kiểm tra toàn kỳ bao gồm ranh giới; không suy đủ phiên từ min/max hay ngày làm việc thông thường. Đây là lịch tham chiếu, chưa phải xác thực độc lập lịch gốc Nasdaq. Sai lệch tương lai cần đối chiếu nguồn sàn.

## Cảnh báo giữ lại để điều tra

| Ngày | Return một phiên, xấp xỉ |
|---|---:|
| 2020-03-13 | +11,98% |
| 2020-03-16 | -12,86% |
| 2020-03-24 | +10,03% |
| 2020-07-31 | +10,47% |
| 2025-04-09 | +15,33% |

Ngưỡng 10% chỉ dùng gắn cờ, không tuning hoặc kết luận nguyên nhân. Giữ cả 5 dòng; giải thích có nguồn thuộc hạng mục 8.

## Implementation và bằng chứng

- Logic dùng chung tại `backend/data/validation/validator.py`, gọi từ notebook. Validator chặn xuất nếu chất lượng không đạt và từ chối ghi đè validated/report có sẵn.
- Report audit mới: `data/metadata/aapl_quality_audit_aapl_2015_2025_acq_20261119T141302002415Z.json`.
- Notebook: `notebooks/01_AAPL_Data_Exploration.ipynb`, mục TV1 số 5, đã chạy thành công.
- Tests: đặt `TV1_DATASET_VERSION=aapl_2015_2025_acq_20261119T141302002415Z`, chạy `python -m unittest discover -s tests/data -v`: **20/20 đạt, không skip**. Bao gồm 7 test chất lượng với nhiều subcase: thiếu phiên đầu/giữa/cuối, cuối tuần/ngày lễ, schema/rỗng, giá lỗi, thứ tự/trùng, OHLCV và cảnh báo không xóa dòng; 13 test còn lại kiểm tra pipeline/provenance/versioning.
- Không tải dữ liệu mới, không fit scaler hoặc training; bản ZIP đầy đủ đã chia sẻ giữ nguyên. Audit bổ sung được bàn giao riêng trên Drive, không giả nhận là validation report cũ trong ZIP.

[Audit JSON trên Drive Project_CW](https://drive.google.com/file/d/1LPODQyDN2koGdSYpKYPMUSh-NEYAPEq_/view?usp=drivesdk) đã upload và đọc lại metadata xác nhận đúng thư mục. Đây là kết quả của lần chạy nêu trên; chạy lại notebook sẽ ghi timestamp audit mới cục bộ.
