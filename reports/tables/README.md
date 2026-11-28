Bảng kết quả từ Evaluation; không tự tính lại khác quy tắc.

Mục10 bổ sung bảng CSV để đọc và nộp báo cáo mà không cần mở toàn bộ logs nghiên cứu:

- `TV6_Final_Comparison.csv`: H1 và H5 overall, mean/std các seed đã chốt.
- `TV6_Final_Per_Horizon.csv`: đủ từng horizon và overall; persistence không bị nhân thành ba seed.
- `TV6_Final_Per_Seed.csv`: kết quả từng seed và số mẫu/errors.
- `TV6_Final_Tables_Provenance.json`: hash nguồn và bảng xuất.

Xuất lại bằng `scripts/export_tv6_report_tables.py` khi có đủ evidence gốc; không train hoặc đổi metric. Original locked test và post-development old test luôn tách phase; không gọi residual là test độc lập mới.
