# TV1 — hạng mục 2: bàn giao snapshot

## Bộ bàn giao hiện tại — đủ artifacts

Đã xuất validated CSV/report, kiểm tra và upload gói đầy đủ. Phần chuẩn bị và cung cấp bộ file đã hoàn thành; xác nhận của người nhận ở máy khác vẫn đang chờ. Audit chất lượng mở rộng/lịch phiên vẫn theo hạng mục 5, không được coi hoàn thành chỉ vì đã xuất validated.

- [ZIP đầy đủ trên Drive](https://drive.google.com/file/d/1gfVBtM81snGI6x4rhqkAX6JZE9wavSfY/view?usp=drivesdk).
- [Checksum ZIP đầy đủ](https://drive.google.com/file/d/1j6nN6gRB_xzGvnxbt-fmmHqGSjr_iMM4/view?usp=drivesdk).
- Local: `artifacts/releases/aapl_2015_2025_acq_20261119T141302002415Z_complete_handoff_20261119T151339704353Z.zip`.
- SHA-256 ZIP: `1aa67d814e5d68b3f275af88443dd31835974463dee1527cb747c049d7f7ea07`.
- Receipt hiện tại: `data/metadata/aapl_handoff_aapl_2015_2025_acq_20261119T141302002415Z_complete.json`.
- Nội dung: raw CSV, validated CSV bốn cột, metadata nguồn, validation report, script verify, manifest và HANDOFF.txt.
- Validator đã chạy thật: passed; 2.766 dòng raw và 2.766 dòng validated. Đối chiếu từng ngày/giá đạt; raw và metadata nguồn giữ nguyên hash. Hash validated: `ee56f9c782ac9e938985c680a9015d1ae198982e7d1cddc49ee5d67630c7b16d`.
- Hai upload thành công và metadata Drive xác nhận đúng thư mục Project_CW. Không xóa gói raw trước đó, không đổi quyền chia sẻ.

## Hướng dẫn nhận và xác minh

1. Tải ZIP đầy đủ và checksum qua hai link trên; không tải lại Yahoo để thay snapshot.
2. Từ source project, chạy `python scripts/verify_tv1_handoff.py --archive <zip> --checksum <zip.sha256>`. Script chỉ dùng thư viện chuẩn; kiểm tra ZIP checksum/CRC, path/membership, hash/kích thước từng file, raw/metadata/report/validated linkage và từng dòng giá/ngày.
3. Giải nén vào bản project mới, giữ nguyên đường dẫn tương đối; không ghi đè file có hash khác. Không cần training hoặc scaler để xác minh.
4. Người nhận gửi version, ZIP hash và output `passed: true`. Chưa có xác nhận thực tế này; kiểm tra cục bộ không thay thế nó.

Notebook hiển thị bộ đầy đủ, trạng thái upload, kết quả verify và dữ liệu validated mẫu. Chạy lại notebook không chạy lại validator để ghi đè validated.

## Lịch sử — gói raw trước khi có validated

Trạng thái ở thời điểm đóng gói raw trước đây: đã chuẩn bị, kiểm tra và upload gói raw cùng checksum; khi đó chưa có validated/report. Các đường dẫn dưới giữ cho truy vết, không phải gói bàn giao hiện tại.

- Version: `aapl_2015_2025_acq_20261119T141302002415Z`.
- ZIP: `artifacts/releases/aapl_2015_2025_acq_20261119T141302002415Z_raw_handoff_20261119T143608193280Z.zip`.
- SHA-256 ZIP: `bcb25cf2ec7b4653b9c812bbd3ef009a9eb83b2873ffee5997a050c291e12e38`.
- Receipt: `data/metadata/aapl_handoff_aapl_2015_2025_acq_20261119T141302002415Z.json`.
- Nội dung: raw CSV, metadata, manifest hash/kích thước từng file, HANDOFF.txt. Đã kiểm tra ZIP CRC và hash từng file trong ZIP.
- Người nhận đối chiếu checksum ZIP với `.zip.sha256`, giải nén vào gốc repo giữ đường dẫn, xác minh từng file theo manifest; không ghi đè file khác hash. Artifacts không commit Git.
- Còn thiếu: validated CSV, validation report; chờ kiểm định ở hạng mục tiếp theo, không tự tạo bằng chứng đạt.
- Thư mục bàn giao hiện tại và cho các lần tiếp theo theo yêu cầu người dùng: [Project_CW](https://drive.google.com/drive/folders/16HyJmtmQ0YzfGHAGGtQ_qTSNEc6lQMwl).
- [Gói ZIP trên Drive](https://drive.google.com/file/d/1mNgFwUGtfb7V7XR_DQ-QhiQ2J23kN9sl/view?usp=drivesdk).
- [Checksum SHA-256 trên Drive](https://drive.google.com/file/d/1-gjjd0XRNgsyhm8qcfSj5G7Dp2Txl7y-/view?usp=drivesdk).
- Cả hai upload thành công; đọc lại metadata xác nhận đúng thư mục cha. Không thay đổi quyền chia sẻ. Chưa tải lại để đối chiếu byte trên Drive; checksum và hash nội dung ZIP đã kiểm tra cục bộ.
- Chưa có xác nhận người nhận đã tải và kiểm tra thành công. Notebook đã ghi trạng thái và đối chiếu gói cục bộ.
