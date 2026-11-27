# TV1 — hạng mục 6: nghiệm thu đầu ra chuẩn theo flow

Flow: snapshot raw cố định → provenance → audit chất lượng mục 5 → nghiệm thu bảng chuẩn mục 6 → khám phá mục 7/điều tra mục 8 → bàn giao cho TV2. Validated đã xuất khi hoàn thiện bộ bàn giao mục 2; lần này không xuất lại hoặc ghi đè file.

## Kết quả đã thực thi 19/11/2026

Version `aapl_2015_2025_acq_20261119T141302002415Z`: **14/14 kiểm tra đạt**, raw và validated cùng 2.766 dòng. Schema đúng thứ tự `date,ticker,adjusted_close,dataset_version`; mọi ticker AAPL, mọi version khớp; ngày hợp lệ/duy nhất/tăng dần và khớp raw từng dòng; giá finite/dương, bằng Adj Close USD với rtol/atol 1e-12.

Ánh xạ: raw.date → date; AAPL → ticker; raw.Adj Close → adjusted_close; version nguồn → dataset_version. Không xóa/điền/chuẩn hóa/làm tròn giá, chia tập hoặc windowing. Các cột OHLCV khác giữ tại raw, không đưa thêm vào bảng model.

Kiểm tra phụ thuộc audit chất lượng mục 5 đạt và hash raw/metadata đúng; validation report liên kết đúng raw, metadata và validated. Hash cả năm file được ghi trong audit output, bao gồm hash báo cáo chất lượng của lần chạy tương ứng. Không dùng báo cáo khác snapshot để nghiệm thu.

- Raw hash giữ nguyên: `cbcadbc002d05bc27a573114b9bb73b930733585b7823d147ca3477354479351`.
- Metadata hash giữ nguyên: `71213959ec9c111a1826db9058dc41f61772af9a0324a4e32ff61eb3bf0edc24`.
- Validated hash giữ nguyên: `ee56f9c782ac9e938985c680a9015d1ae198982e7d1cddc49ee5d67630c7b16d`.
- Audit: `data/metadata/aapl_standard_output_audit_<dataset_version>.json`.
- Logic: `backend/data/validation/standard_output.py`; notebook mục TV1 số 6 hiển thị kiểm tra, mẫu đầu/cuối và hash.
- Tests: **24/24 đạt, không skip** khi đặt `TV1_DATASET_VERSION` bằng version trên và chạy `python -m unittest discover -s tests/data -v`. Bốn test output mới với nhiều subcase kiểm tra extra column, hash sai, audit khác raw, giá/ngày/ticker/version sai kể cả khi hash file được cập nhật.

Lịch phiên vẫn có giới hạn tham chiếu NASDAQ alias XNYS như mục 5. Năm biến động lớn giữ lại chờ điều tra mục 8. Chưa fit scaler/train; chưa có xác nhận người nhận độc lập.

## Bàn giao bằng chứng

- [Audit đầu ra chuẩn trên Drive](https://drive.google.com/file/d/1-_5i4wI_n71WHU0WHoYel3PvDpKc5gWu/view?usp=drivesdk).
- [Audit chất lượng cùng lần chạy để đối chiếu hash](https://drive.google.com/file/d/1Rv91BwQXd3ysK5ifAgscFyOkvH6dNV1X/view?usp=drivesdk).

Đã upload và đọc lại metadata xác nhận đúng thư mục Project_CW. Giữ các bản cũ trên Drive; chạy lại notebook có thể tạo timestamp/hash báo cáo audit mới, không thay hash dataset.
