## Tổng kết hiện hành — audit mục10, 28/11/2026

Snapshot hiện hành `2766` phiên,version `aapl_2015_2025_acq_20261119T141302002415Z`,2015-01-02–2025-12-31. Yahoo/yfinance,auto_adjust=False,chọn Adj Close làm adjusted_close. Bảng chuẩn date/ticker/adjusted_close/dataset_version; USD.

Train target2015–2022,val2023,test2024–2025; scaler chỉfit2014 giá train. H1:train1984/val250/test502 windows; H5:train1980/val246/test498. Giữ lịch sử quan sát từ split trước; cả5 target cùngsplit. Audit toàn bộ prepared/statistics/hash nguồn đạt, không sửa snapshot.

Snapshot điều chỉnh hồi cứu không point-in-time. Nguồn dự phòng vận hành là snapshot/hash đã khóa; đây không phải nguồn thay thế được cấp phép. Chưa có bằng chứng quyền phân phối công khai dataset. Xem docs/TV6_Data_Use_and_Limits.md.

---

## Lịch sử các giai đoạn — không dùng làm trạng thái hiện tại

# Dữ liệu mẫu và mô tả

## Cập nhật đã kiểm chứng trên snapshot hiện tại — 19/11/2026

**Kết luận audit lại:** phần dữ liệu TV1 đạt các kiểm tra tại máy, sẵn sàng chuyển bảng chuẩn cho TV2; còn chờ xác nhận người nhận/máy khác ở mục 2 và 10. Suite mới nhất 34/34 đạt sau bổ sung hồi quy lỗi ghi report; dữ liệu nguồn và validated không đổi. [Audit đầy đủ 10 hạng mục](audits/TV1_Final_Audit.md) và phần tổng audit ngay đầu notebook là kết quả hiện hành; các báo cáo theo run phía dưới giữ lịch sử.

Snapshot đang dùng: `aapl_2015_2025_acq_20261119T141302002415Z`, khác version cũ trong phần báo cáo PR giữ phía dưới. Notebook đã thực thi các bước thu thập, metadata, bảo vệ snapshot, kiểm tra chất lượng và nghiệm thu bảng bốn cột; EDA hạng mục 7 dùng đúng snapshot này.

Có 2.766 phiên (2015-01-02–2025-12-31), 2.765 return. Median giá 88,16 USD; min/max 20,53/285,20 USD. Median theo năm 2015 và 2025 lần lượt 26,89 và 228,86 USD, cho thấy mức giá khác theo giai đoạn. Return phân vị 1%–99% khoảng -4,81% đến +4,94%; 5 phiên absolute return >10% giữ nguyên để điều tra mục 8. Đây là mô tả dữ liệu, không dùng để tuning trên test hoặc kết luận nguyên nhân.

Chi tiết hình/bảng, run ID và giới hạn: [báo cáo EDA](audits/TV1_Data_Exploration.md), [notebook](../notebooks/01_AAPL_Data_Exploration.ipynb). Hash raw hiện tại `cbcadbc002d05bc27a573114b9bb73b930733585b7823d147ca3477354479351`; validated `ee56f9c782ac9e938985c680a9015d1ae198982e7d1cddc49ee5d67630c7b16d`. TV2 preprocessing chưa được thực hiện trong EDA.

Hạng mục 8 đã đối chiếu 5/5 phiên return >10% với Close/Adj Close và bối cảnh có nguồn; chưa có bằng chứng cần sửa giá, giữ toàn bộ dòng. Xem [báo cáo điều tra](audits/TV1_Anomaly_Review.md), ledger nguồn và mục 8 notebook. Kết luận bối cảnh không phải xác định nguyên nhân duy nhất.

## Nội dung PR TV1 ban đầu — giữ để truy vết, không phải snapshot hiện tại

> Ghi chú tiếp nhận cục bộ 19/11/2026: nội dung dưới đây được lấy từ TV1 PR #5, commit `08675d823bd2499df1508dc4b4cde8722d557629`. Các thống kê, hash và kết quả 4/4 là do TV1 báo cáo, chưa được xác minh trên snapshot gốc ở workspace này vì chưa nhận artifacts. Snapshot EDA mới trong notebook là bộ riêng, không thay thế bằng chứng bàn giao TV1.

Trạng thái theo tác giả PR ban đầu: đã hoàn thành và kiểm chứng version `aapl_2015_2025_v1`; tuyên bố và số liệu lịch sử dưới đây chưa được xác minh trên artifacts gốc của version đó tại workspace này. Số liệu đang dùng nằm ở phần cập nhật đầu file. TV2 preprocessing/windowing không thuộc phần việc đã nghiệm thu TV1.

## Nội dung cần hoàn thiện

### 1. Nguồn dữ liệu và phạm vi thu thập (TV1)
- **Mã chứng khoán:** `AAPL` (Apple Inc.).
- **Nguồn thu thập:** Yahoo Finance, tải tự động bằng thư viện Python `yfinance` phiên bản `1.8.0`.
- **Phạm vi ngày yêu cầu:** `2015-01-01` đến `2025-12-31`.
- **Phạm vi phiên giao dịch thực tế:** Từ phiên `2015-01-02` đến hết phiên `2025-12-31` (tổng cộng **2.766** phiên giao dịch theo lịch mở cửa thực tế của sàn, không tự cộng ngày lịch cuối tuần hoặc ngày lễ).
- **Đơn vị đo:** `USD`.
- **Phiên bản dữ liệu (`dataset_version`):** `aapl_2015_2025_v1`.
- **Thời điểm thực hiện (UTC):**
  - Thu thập (`acquisition`): `2026-11-19T05:37:13.285635+00:00`
  - Kiểm định (`validation`): `2026-11-19T05:39:47.319484+00:00`

### 2. Chính sách điều chỉnh giá và giới hạn hồi cứu (TV1)
- **Chính sách điều chỉnh giá (`adjustment_policy`):** Dữ liệu gốc được tải với tham số `auto_adjust=False` để lưu nguyên bản tất cả các trường từ nguồn (`Date`, `Adj Close`, `Close`, `High`, `Low`, `Open`, `Volume`). Cột `Adj Close` (giá đóng cửa đã điều chỉnh chia tách cổ phiếu và cổ tức bởi Yahoo Finance) được chọn làm đặc trưng và biến mục tiêu duy nhất với tên chuẩn hóa `adjusted_close`.
- **Giới hạn điều chỉnh hồi cứu (Point-in-time limitation):** Chuỗi giá `Adj Close` trên Yahoo Finance được tính toán điều chỉnh hồi cứu tại thời điểm tải dữ liệu (`2026-11-19`), không phản ánh nguyên trạng mức giá giao dịch tại từng thời điểm trong quá khứ (non-point-in-time). Giới hạn này được lưu cố định trong metadata để đảm bảo tính minh bạch khi đánh giá mô hình.

### 3. Thống kê mô tả và phân bố phiên theo giai đoạn chia tập (TV1)
Thống kê trên **2.766** phiên hợp lệ của cột `adjusted_close` (đơn vị: `USD`):
- **Giá thấp nhất (Min):** `20.532545` USD
- **Giá cao nhất (Max):** `285.196411` USD
- **Giá trung bình (Mean):** `105.955528` USD
- **Độ lệch chuẩn (Std):** `74.063170` USD

Số lượng phiên giao dịch theo các mốc thời gian chia tập đã chốt:
- **Giai đoạn Train (2015–2022):** `2.014` phiên
- **Giai đoạn Validation (2023):** `250` phiên
- **Giai đoạn Test (2024–2025):** `502` phiên

### 4. Cấu trúc bảng dữ liệu chuẩn và dữ liệu mẫu (TV1)
Bảng dữ liệu sau kiểm định tuân thủ hợp đồng dữ liệu gồm 4 cột (`date`, `ticker`, `adjusted_close`, `dataset_version`), định dạng ngày `YYYY-MM-DD`:

**5 phiên giao dịch đầu tiên (năm 2015):**

| date | ticker | adjusted_close | dataset_version |
|---|---|---:|---|
| 2015-01-02 | AAPL | 24.153406 | aapl_2015_2025_v1 |
| 2015-01-05 | AAPL | 23.472965 | aapl_2015_2025_v1 |
| 2015-01-06 | AAPL | 23.475176 | aapl_2015_2025_v1 |
| 2015-01-07 | AAPL | 23.804350 | aapl_2015_2025_v1 |
| 2015-01-08 | AAPL | 24.718960 | aapl_2015_2025_v1 |

**5 phiên giao dịch cuối cùng (năm 2025):**

| date | ticker | adjusted_close | dataset_version |
|---|---|---:|---|
| 2025-12-24 | AAPL | 272.859406 | aapl_2015_2025_v1 |
| 2025-12-26 | AAPL | 272.450806 | aapl_2015_2025_v1 |
| 2025-12-29 | AAPL | 272.809601 | aapl_2015_2025_v1 |
| 2025-12-30 | AAPL | 272.131927 | aapl_2015_2025_v1 |
| 2025-12-31 | AAPL | 270.916168 | aapl_2015_2025_v1 |

### 5. Tiền xử lý, chuẩn hóa và tạo cửa sổ trượt (TV2)
- *Chưa kiểm chứng — chờ TV2 triển khai `backend/data/preparation/` và `backend/data/transforms/` để bổ sung số lượng mẫu cửa sổ 1 phiên / 5 phiên cho từng tập Train/Validation/Test, tham số `StandardScaler` fit trên tập Train và bằng chứng audit chống rò rỉ dữ liệu.*

---

## Bằng chứng

### 1. Định danh tệp và mã băm toàn vẹn (SHA-256)
Các tệp dữ liệu được lưu cục bộ trong thư mục `data/` (loại trừ khỏi Git theo `.gitignore` và chia sẻ qua kênh lưu trữ nội bộ của nhóm):
- **Snapshot gốc:** `data/raw/aapl_raw_aapl_2015_2025_v1.csv`
  - `SHA-256`: `257de6d2ad3f086e61dba3e6298f805ee52a82b540cc0c0c0bd330c352331838`
- **Dữ liệu đã kiểm định:** `data/validated/aapl_validated_aapl_2015_2025_v1.csv`
  - `SHA-256`: `72fe263b25d61bce1e5590f6fe053992b2a4696bdf46031282094ea87208b834`
- **Metadata nguồn:** `data/metadata/aapl_metadata_aapl_2015_2025_v1.json`
- **Báo cáo kiểm định:** `data/metadata/aapl_validation_report_aapl_2015_2025_v1.json`

### 2. Kết quả kiểm tra chất lượng và kiểm thử đơn vị
- **Kiểm tra dữ liệu (`backend/data/validation/validator.py`):** Trạng thái `passed: true`; `duplicate_date_count: 0`; `missing_price_count: 0`; `non_positive_count: 0`; `is_monotonic_increasing: true`; `raw_sha256_verified: true`.
- **Kiểm thử tự động (`tests/data/test_data_pipeline.py`):** Chạy lệnh `python -m unittest discover -s tests/data -v` đạt **4/4** test cases (`OK`), xác nhận khả năng phát hiện ngày trùng lặp, giá trị không dương, đúng cấu trúc 4 cột và toàn vẹn SHA-256 của bộ dữ liệu thật.
- **Lệnh tái lập pipeline dữ liệu:**
  1. `python -m backend.data.acquisition.downloader`
  2. `python -m backend.data.validation.validator`
  3. `python -m unittest discover -s tests/data -v`
