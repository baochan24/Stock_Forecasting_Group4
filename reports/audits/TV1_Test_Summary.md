# TV1 — hạng mục 9: tổng hợp kiểm thử

## Kết quả thực thi

Run `20261119T154908909974Z`, snapshot `aapl_2015_2025_acq_20261119T141302002415Z`: **33/33 test methods đạt, 0 failure, 0 error, 0 skip**. Nhiều test còn có subcase. Python 3.13.7; NumPy 2.4.4, pandas 3.0.6, yfinance 1.8.0, exchange_calendars 4.13.3.

| Nhóm | Số test methods | Phạm vi |
|---|---:|---|
| Pipeline cơ bản và artifacts thật | 4 | Schema, duplicate, giá lỗi, hash và bảng validated thật |
| Chất lượng | 7 | Rỗng/cột thiếu, ngày sai/trùng/thứ tự, NaN/Inf/giá không dương, phiên đầu/giữa/cuối thiếu, ngày nghỉ, OHLCV, cảnh báo không xóa dòng |
| Provenance | 4 | Metadata đúng/sai/thiếu, raw bị sửa |
| Bảo vệ phiên bản | 5 | Version trùng/bộ dở, file xuất hiện đồng thời, version mới, lỗi mạng và rollback file mới |
| Bảng chuẩn | 4 | Schema/hash, audit cũ, giá/ngày/ticker/version sai ngay cả khi hash file đã cập nhật |
| Gói bàn giao | 6 | ZIP thật hợp lệ; checksum sai, ZIP/member bị sửa, thiếu member, unsafe path bị từ chối |
| Pipeline offline tích hợp | 3 | Download mock → validation → nạp lại/đối chiếu; từ chối ghi đè; raw/metadata bị sửa dừng trước output |

## Bằng chứng

- `logs/audit/tv1_tests_20261119T154908909974Z/summary.json`.
- `logs/audit/tv1_tests_20261119T154908909974Z/unittest.log` (UTF-8).
- Summary ghi kết quả từng test, Python/dependencies, hash log, source backend/data + tests/data và hash artifacts.
- Hash raw, metadata, validated và validation report trước/sau không đổi. Tests làm hỏng dữ liệu/ZIP chỉ ở bản sao trong thư mục tạm. Pipeline tổng hợp được gắn nhãn, không gọi Yahoo/Drive.
- Notebook mục 9 đã cập nhật trực tiếp, đọc lần chạy mới nhất đúng dataset version và kiểm tra hash log/source/artifacts. Không tự chạy lại suite khi Run All; không lùi về lần pass cũ nếu lần chạy mới thất bại.
- Lần chạy trước `20261119T154738792964Z` có suite đạt nhưng stdout bị lỗi encoding Windows; đã sửa runner xuất UTF-8, chạy lại có exit code 0. Không xóa log cũ hoặc dùng lần đó làm nghiệm thu cuối.

## Tái chạy

Từ gốc repo: `.venv/eda/Scripts/python.exe scripts/run_tv1_checks.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z`. Cần snapshot và complete-handoff receipt/ZIP đã bàn giao. Runner lưu thư mục log mới, exit code khác 0 nếu fail/error/skip hoặc artifacts thay đổi. Logs bị Git bỏ qua; bàn giao bản sao có chủ đích cùng report khi cần.

Kết quả chỉ nghiệm thu TV1 trên máy hiện tại, không chứng minh các phần TV2 preprocessing/windowing/scaler hoặc model/train đã đúng. Calendar vẫn là NASDAQ alias XNYS theo thư viện; không xác thực độc lập sàn. Chưa có xác nhận chạy trên máy thành viên khác. Hạng mục tiếp theo là 10: tài liệu và tái lập/bàn giao.

## Bản sao Drive

Sau khi xác nhận mục 9 đã lưu trong notebook workspace và không lỗi cell, đã upload [gói bằng chứng kiểm thử](https://drive.google.com/file/d/1kRarCJ-qP9FN4SVq2jSTWDDdMXmVD2aJ/view?usp=drivesdk) cùng [checksum](https://drive.google.com/file/d/1Wc-r5xwu7HRRa8uKExgWjx9ukYe97Z5w/view?usp=drivesdk); metadata readback xác nhận thư mục Project_CW. ZIP gồm 16 file (log/summary, notebook, báo cáo, runner và source/test được hash) cùng manifest. SHA-256 `41c439bccc0e0a93c9805ae502268fbd040f1945824cf3d782cce1c94efd89e4`. Báo cáo trong ZIP chưa chứa đoạn link bổ sung này; kết quả suite không đổi.
