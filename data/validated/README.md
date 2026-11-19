# data/validated

Bảng hợp lệ sau kiểm tra.

Snapshot hiện tại: `aapl_validated_aapl_2015_2025_acq_20261119T141302002415Z.csv`, đã xuất từ raw bằng validator; 2.766 dòng, schema `date,ticker,adjusted_close,dataset_version`. Giữ giá Adj Close gốc USD, ngày/thứ tự và toàn bộ dòng; không scaler/windowing. File được .gitignore loại khỏi Git; nhận qua gói đầy đủ trên Drive được ghi tại `reports/audits/TV1_Snapshot_Handoff.md`.

Hạng mục 6 kiểm tra lại bằng `backend/data/validation/standard_output.py`, dựa trên audit chất lượng hạng mục 5. Không ghi đè CSV/report đã có. Bằng chứng tại `data/metadata/aapl_standard_output_audit_<dataset_version>.json` và notebook.
