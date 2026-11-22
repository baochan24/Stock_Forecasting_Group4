# artifacts/releases

TV2 preprocessing handoff local: `TV2_Handoff_20261122T145943242978Z.zip` và `.zip.sha256`; chưa là model release phục vụ web. Gói có source chọn lọc, requirements/tests/docs, 5 artifacts TV1, scaler cũ và prepared modes1/5. SHA và bằng chứng tại reports/audits/TV2_Final_Handoff.md. Chưa upload, chưa xác nhận thành viên khác chạy; không commit ZIP/output.

Release manifest liên kết dataset/models/scalers/config/results; web đọc, không tự ghi đè.

Hiện chưa có dữ liệu/kết quả thật.

Gói `<dataset_version>_raw_handoff_<timestamp>.zip` là gói bàn giao dữ liệu raw/metadata tạm thời, không phải release model dùng cho web. Gói chứa manifest hash từng file và HANDOFF.txt; checksum ZIP nằm ở file `.zip.sha256` đi kèm. Output bị Git bỏ qua. Kênh bàn giao là [Drive Project_CW](https://drive.google.com/drive/folders/16HyJmtmQ0YzfGHAGGtQ_qTSNEc6lQMwl); gói raw TV1 và checksum đã upload, chưa có xác nhận người nhận. Receipt của lần chuẩn bị nằm trong `data/metadata/aapl_handoff_<dataset_version>.json`.
