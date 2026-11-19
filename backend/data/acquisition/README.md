# data/acquisition

Tải dữ liệu và metadata nguồn. Giữ bản gốc; ghi chính sách điều chỉnh và hash.

## Implementation và cách chạy

`downloader.py` được tiếp nhận từ TV1 PR #5. Hàm `download_aapl_snapshot(dataset_version=..., raw_dir=..., metadata_dir=...)` tải AAPL ngày 2015–2025 với `auto_adjust=False`, lưu các cột giá/khối lượng và metadata nguồn, chính sách điều chỉnh hồi cứu, SHA-256. Dependencies: `yfinance==1.8.0`, pandas, certifi (xem bộ dependencies EDA hiện có tại `notebooks/requirements-eda.txt`).

Từ gốc repo, trong Python đã cài dependencies:

```python
from backend.data.acquisition.downloader import download_aapl_snapshot

metadata = download_aapl_snapshot(dataset_version="aapl_2015_2025_<unique_id>")
```

Luôn chọn version mới. Downloader tự từ chối nếu raw hoặc metadata đích đã tồn tại trước khi gọi mạng; dùng exclusive creation `x` cho cả hai file để chống ghi đè khi chạy đồng thời. Lỗi được bắt sẽ dọn chỉ file do chính lần gọi tạo. Tiến trình bị tắt đột ngột có thể để lại file dở; không tự ghi đè hoặc xóa để thử lại. Tên version chỉ dùng chữ, số, `_`, `-`. Không dùng lại version trong báo cáo TV1 cho snapshot mới.

## Lần thu thập đã thực hiện

- Ngày 19/11/2026, đã chạy downloader thật, tạo version `aapl_2015_2025_acq_20261119T141302002415Z`.
- Kết quả: 2.766 dòng, từ 2015-01-02 đến 2025-12-31; raw ở `data/raw/`, metadata ở `data/metadata/`.
- Đây là snapshot mới thu thập trong phiên làm việc, không phải artifacts TV1 đã báo cáo trước đó và không phải snapshot EDA cũ.
- Bằng chứng và hash: `reports/audits/TV1_Acquisition_20261119T141302002415Z.md`.
- Chỉ hoàn thành bước download và kiểm tra tính nhất quán file/metadata. Chưa validation, làm sạch, fit scaler hoặc windowing.
