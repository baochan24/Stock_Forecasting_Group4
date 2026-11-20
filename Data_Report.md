# BÁO CÁO MÔ TẢ VÀ KIỂM ĐỊNH GÓI DỮ LIỆU CỔ PHIẾU AAPL (2015–2025)

- **Mã định danh phiên bản (`dataset_version`):** `aapl_2015_2025_v1`
- **Đối tượng nghiên cứu:** Cổ phiếu Apple Inc. (`AAPL` — Sàn NASDAQ)
- **Phụ trách thực hiện:** Thành viên 1 (TV1 — Thu thập, kiểm định và đóng gói dữ liệu)
- **Trạng thái kiểm định:** Đã hoàn tất và xác thực toàn vẹn (`passed: true`), đủ điều kiện bàn giao cho Thành viên 2 (TV2) thực hiện tiền xử lý và tạo cửa sổ trượt.

---

## 1. Mục đích và Kiến trúc gói dữ liệu (`data/`)

Gói dữ liệu này đóng vai trò là nguồn dữ liệu đầu vào gốc duy nhất (Single Source of Truth) cho toàn bộ quy trình nghiên cứu dự báo chuỗi thời gian của Nhóm 4 (từ bước tiền xử lý, huấn luyện mô hình LSTM/CNN 1D đến đánh giá baseline và trình diễn hệ thống). Theo chính sách quản lý mã nguồn `.gitignore`, toàn bộ thư mục `data/` được loại trừ khỏi kho lưu trữ Git và được đồng bộ nội bộ giữa các thành viên kèm mã băm mật mã **SHA-256** nhằm bảo đảm tính nhất quán tuyệt đối của dữ liệu thực nghiệm.

Cấu trúc chi tiết bên trong thư mục `data/`:

```text
data/
├── DATA_REPORT.md                                              # Tài liệu báo cáo mô tả và bằng chứng kiểm định dữ liệu
├── raw/
│   └── aapl_raw_aapl_2015_2025_v1.csv                          # Bản chụp dữ liệu thô nguyên bản từ Yahoo Finance (7 cột, 2.766 dòng)
├── validated/
│   └── aapl_validated_aapl_2015_2025_v1.csv                    # Bảng dữ liệu sạch chuẩn hợp đồng (4 cột, 2.766 dòng) — đầu vào cho TV2
└── metadata/
    ├── aapl_metadata_aapl_2015_2025_v1.json                    # Siêu dữ liệu nguồn tải, chính sách điều chỉnh giá và mã hash tệp raw
    └── aapl_validation_report_aapl_2015_2025_v1.json           # Báo cáo kết quả kiểm tra chất lượng và mã hash tệp validated
```

---

## 2. Nguồn thu thập, Quy trình tải và Siêu dữ liệu (Data Acquisition)

### 2.1. Thông số thu thập dữ liệu
Quá trình thu thập được thực thi tự động thông qua module độc lập `backend/data/acquisition/downloader.py` với các tham số kỹ thuật được khóa cố định:

| Tham số / Thuộc tính | Giá trị thiết lập | Giải thích kỹ thuật |
| :--- | :--- | :--- |
| **Mã chứng khoán (`ticker`)** | `AAPL` | Đại diện cổ phiếu Apple Inc. có thanh khoản cao và lịch sử giao dịch liên tục. |
| **Nguồn dữ liệu (`source`)** | Yahoo Finance | Truy xuất qua thư viện Python `yfinance` phiên bản `1.8.0`. |
| **Tần suất lấy mẫu (`interval`)** | `1d` (Theo ngày) | Lấy giá tổng kết theo từng phiên giao dịch chính thức trong ngày. |
| **Khung ngày yêu cầu** | `2015-01-01` $\rightarrow$ `2025-12-31` | Tham số truyền vào API là `start="2015-01-01"`, `end="2026-01-01"` (do biên trên `end` của `yfinance` mang tính loại trừ). |
| **Khung phiên thực tế** | `2015-01-02` $\rightarrow$ `2025-12-31` | Phiên giao dịch đầu tiên của năm 2015 là ngày `2015-01-02` (ngày `2015-01-01` là nghỉ Tết Dương lịch). |
| **Tổng số bản ghi** | `2.766` phiên | Đúng bằng số ngày mở cửa thực tế của sàn giao dịch Mỹ trong 11 năm (2015–2025). |
| **Đơn vị tiền tệ (`currency`)** | `USD` | Đô la Mỹ. |
| **Thời điểm tải (UTC)** | `2026-11-19T05:37:13.285635+00:00` | Mốc thời gian ghi nhận chính xác lúc tạo bản chụp `raw`. |

### 2.2. Quy tắc xử lý trục thời gian và Khả năng tái lập môi trường
- **Bảo toàn lịch phiên giao dịch thực tế:** Cột thời gian được chuẩn hóa về định dạng chuỗi ISO `YYYY-MM-DD`. Hệ thống giữ nguyên trục thời gian theo các phiên giao dịch thực tế có trong dữ liệu gốc, tuyệt đối không tự chèn thêm các ngày lịch cuối tuần (Thứ Bảy, Chủ Nhật) hoặc ngày nghỉ lễ của thị trường để tránh làm sai lệch bước nhảy chuỗi thời gian (`horizon_step`).
- **Bảo toàn dữ liệu nguyên bản:** Tệp `data/raw/aapl_raw_aapl_2015_2025_v1.csv` lưu giữ nguyên trạng 7 cột trả về từ Yahoo Finance (`date`, `Adj Close`, `Close`, `High`, `Low`, `Open`, `Volume`) mà không thực hiện bất kỳ thao tác làm tròn hay sửa đổi âm thầm nào.
- **Tương thích hệ điều hành:** Module thu thập tích hợp sẵn cơ chế tự động sao chép chứng chỉ bảo mật SSL (`certifi`) sang thư mục tạm chuẩn ASCII khi chạy trên Windows có đường dẫn chứa ký tự Unicode/tiếng Việt, giúp khắc phục triệt để lỗi `UnicodeEncodeError` của thư viện mạng bên dưới `yfinance`.

---

## 3. Chính sách điều chỉnh giá và Giới hạn hồi cứu (Adjustment Policy)

Trong giai đoạn 2015–2025, cổ phiếu `AAPL` trải qua các sự kiện doanh nghiệp làm thay đổi mệnh giá danh nghĩa (điển hình là đợt chia tách cổ phiếu tỷ lệ 4:1 vào tháng 8/2020) cùng các kỳ chi trả cổ tức tiền mặt định kỳ. Việc sử dụng giá đóng cửa thông thường (`Close`) sẽ tạo ra các điểm đứt gãy nhân tạo lớn tại ngày giao dịch không hưởng quyền, gây nhiễu nghiêm trọng cho bài toán dự báo hồi quy.

Do đó, gói dữ liệu áp dụng quy tắc xử lý giá như sau:
1. **Chính sách trích xuất (`auto_adjust=False`):** Hệ thống tải dữ liệu với chế độ `auto_adjust=False` để lưu giữ đồng thời cả giá gốc (`Close`) và giá đã điều chỉnh (`Adj Close`) trong tệp `raw`, sau đó lựa chọn cột `Adj Close` làm biến đặc trưng và biến mục tiêu duy nhất với tên chuẩn hóa là `adjusted_close`.
2. **Giới hạn điều chỉnh hồi cứu (Point-in-time Limitation):** Chuỗi giá `Adj Close` trên Yahoo Finance được tính toán điều chỉnh hồi cứu tại thời điểm tải dữ liệu (`2026-11-19`), tức toàn bộ lịch sử giá quá khứ đã được quy đổi về mặt bằng cổ phiếu hiện hành chứ không phản ánh nguyên trạng mức giá niêm yết tại từng thời điểm giao dịch trong quá khứ (non-point-in-time). Giới hạn này được ghi nhận công khai trong `aapl_metadata_aapl_2015_2025_v1.json` để đảm bảo tính minh bạch khi diễn giải kết quả mô hình.

---

## 4. Hợp đồng cấu trúc dữ liệu sạch (`data/validated/`)

Tệp `data/validated/aapl_validated_aapl_2015_2025_v1.csv` là đầu ra chuẩn hóa sau bước kiểm định, tuân thủ nghiêm ngặt cấu trúc **4 cột** đã thống nhất trong tài liệu hợp đồng dữ liệu của nhóm:

| Tên cột | Kiểu dữ liệu | Ràng buộc & Quy định định dạng | Vai trò sử dụng |
| :--- | :--- | :--- | :--- |
| `date` | `string` | Định dạng `YYYY-MM-DD`, duy nhất, tăng dần nghiêm ngặt. | Khóa định danh phiên giao dịch và căn chỉnh mốc chia tập thời gian. |
| `ticker` | `string` | Giá trị cố định `AAPL`, không rỗng. | Định danh mã chứng khoán phục vụ đối chiếu và hiển thị. |
| `adjusted_close` | `float64` | Số thực hữu hạn, dương nghiêm ngặt ($> 0$), đơn vị `USD`. | Chuỗi đầu vào (`lookback`) và giá trị mục tiêu (`target`) của mô hình. |
| `dataset_version` | `string` | Giá trị cố định `aapl_2015_2025_v1`. | Truy vết phiên bản dữ liệu xuyên suốt quá trình huấn luyện và đánh giá. |

---

## 5. Phân tích thống kê mô tả và Phân bố theo giai đoạn chia tập

### 5.1. Thống kê mô tả biến `adjusted_close` (2015–2025)
Kết quả tính toán trên toàn bộ **2.766 phiên giao dịch** hợp lệ (đơn vị: `USD`):

| Chỉ số thống kê | Giá trị (USD) | Nhận xét chuyên môn |
| :--- | :---: | :--- |
| **Số lượng quan sát (`count`)** | `2.766` | Đầy đủ $100\%$ số phiên giao dịch trong 11 năm. |
| **Giá thấp nhất (`min`)** | `20.532545` | Mức giá điều chỉnh thấp nhất ghi nhận trong giai đoạn đầu chu kỳ. |
| **Giá cao nhất (`max`)** | `285.196411` | Mức đỉnh giá điều chỉnh ghi nhận ở giai đoạn cuối chu kỳ. |
| **Giá trị trung bình (`mean`)** | `105.955528` | Phản ánh xu hướng tăng trưởng dài hạn của cổ phiếu AAPL. |
| **Độ lệch chuẩn (`std`)** | `74.063170` | Biên độ phân tán lớn do mức giá mở rộng hơn 13 lần từ vùng ~$20 lên >$285. |

*Lưu ý cho bước tiền xử lý (TV2):* Do biên độ giá ở giai đoạn 2024–2025 cao hơn đáng kể so với giai đoạn 2015–2022, bộ chuẩn hóa `StandardScaler` bắt buộc chỉ được `fit` trên tập Train (2015–2022) để chống rò rỉ dữ liệu, đồng thời cần lưu ý đặc điểm ngoại suy biên độ (extrapolation) khi mô hình dự báo trên tập Test.

### 5.2. Phân bố số phiên giao dịch theo quy tắc chia tập tuần tự
Tuân thủ nguyên tắc chia tập theo thứ tự thời gian (không xáo trộn ngẫu nhiên):

| Tập dữ liệu | Khoảng thời gian mục tiêu | Số phiên giao dịch | Tỷ trọng | Mục đích sử dụng |
| :--- | :---: | :---: | :---: | :--- |
| **Train** | `2015-01-01` – `2022-12-31` | `2.014` | `72,81%` | Fit `StandardScaler` và huấn luyện trọng số mô hình. |
| **Validation** | `2023-01-01` – `2023-12-31` | `250` | `9,04%` | Theo dõi early stopping, tinh chỉnh siêu tham số và chọn checkpoint. |
| **Test** | `2024-01-01` – `2025-12-31` | `502` | `18,15%` | Đánh giá hiệu năng độc lập cuối cùng (khóa tuyệt đối trong quá trình tuning). |
| **Tổng cộng** | **`2015-01-02` – `2025-12-31`** | **`2.766`** | **`100,00%`** | Toàn bộ chuỗi phiên giao dịch hợp lệ. |

---

## 6. Dữ liệu mẫu minh họa thực tế

Trích xuất trực tiếp từ tệp `data/validated/aapl_validated_aapl_2015_2025_v1.csv`:

### 6.1. Năm phiên giao dịch đầu tiên (Tháng 01/2015)

| `date` | `ticker` | `adjusted_close` (USD) | `dataset_version` |
| :--- | :---: | :---: | :--- |
| `2015-01-02` | `AAPL` | `24.153406` | `aapl_2015_2025_v1` |
| `2015-01-05` | `AAPL` | `23.472965` | `aapl_2015_2025_v1` |
| `2015-01-06` | `AAPL` | `23.475176` | `aapl_2015_2025_v1` |
| `2015-01-07` | `AAPL` | `23.804350` | `aapl_2015_2025_v1` |
| `2015-01-08` | `AAPL` | `24.718960` | `aapl_2015_2025_v1` |

### 6.2. Năm phiên giao dịch cuối cùng (Tháng 12/2025)

| `date` | `ticker` | `adjusted_close` (USD) | `dataset_version` |
| :--- | :---: | :---: | :--- |
| `2025-12-24` | `AAPL` | `272.859406` | `aapl_2015_2025_v1` |
| `2025-12-26` | `AAPL` | `272.450806` | `aapl_2015_2025_v1` |
| `2025-12-29` | `AAPL` | `272.809601` | `aapl_2015_2025_v1` |
| `2025-12-30` | `AAPL` | `272.131927` | `aapl_2015_2025_v1` |
| `2025-12-31` | `AAPL` | `270.916168` | `aapl_2015_2025_v1` |

---

## 7. Quy trình kiểm định chất lượng và Bằng chứng toàn vẹn

### 7.1. Kết quả kiểm tra tự động (`backend/data/validation/validator.py`)
Tất cả các chốt kiểm soát chất lượng được thực thi lúc `2026-11-19T05:39:47.319484+00:00` và ghi nhận trong `data/metadata/aapl_validation_report_aapl_2015_2025_v1.json`:

| Hạng mục kiểm tra | Chỉ số đo được | Tiêu chuẩn chấp nhận | Kết quả |
| :--- | :---: | :---: | :---: |
| Đối chiếu SHA-256 tệp `raw` với metadata | `raw_sha256_verified = true` | Khớp $100\%$ chuỗi băm | **Đạt** |
| Số bản ghi trùng ngày (`duplicate_date_count`) | `0` | `0` | **Đạt** |
| Số giá trị bị thiếu (`missing_price_count`) | `0` | `0` | **Đạt** |
| Số giá trị không dương (`non_positive_count`) | `0` | `0` | **Đạt** |
| Thứ tự thời gian tăng dần (`is_monotonic_increasing`) | `true` | `true` | **Đạt** |
| Trạng thái tổng thể (`passed`) | `true` | `true` (không có lỗi phát sinh) | **Đạt** |

### 7.2. Kết quả kiểm thử đơn vị (`tests/data/test_data_pipeline.py`)
Bộ kiểm thử tự động gồm 4 ca kiểm thử đã được chạy qua trình kiểm thử chuẩn của Python (`python -m unittest discover -s tests/data -v`) và đạt **4/4 (`OK` trong `0.056s`)**:
1. `test_valid_dataframe_passes`: Kiểm tra khả năng chuẩn hóa bảng dữ liệu hợp lệ về đúng 4 cột chuẩn.
2. `test_duplicate_dates_rejected`: Kiểm tra cơ chế phát hiện và từ chối dữ liệu khi xuất hiện ngày giao dịch trùng lặp.
3. `test_missing_or_non_positive_price_rejected`: Kiểm tra cơ chế phát hiện và chặn dữ liệu có giá trị `NaN` hoặc giá trị $\le 0$.
4. `test_generated_aapl_artifacts_integrity`: Kiểm tra trực tiếp 4 tệp dữ liệu thực tế trên ổ đĩa, xác nhận sự tồn tại của tệp, độ dài 2.766 dòng, biên ngày `2015-01-02` đến `2025-12-31` và sự trùng khớp tuyệt đối của hai mã SHA-256.

### 7.3. Mã băm SHA-256 xác thực tệp tin
Các thành viên trong nhóm khi giải nén gói dữ liệu có thể đối chiếu mã băm dưới đây để xác nhận dữ liệu không bị thay đổi hoặc hỏng hóc:
- **`data/raw/aapl_raw_aapl_2015_2025_v1.csv`:**
  `257de6d2ad3f086e61dba3e6298f805ee52a82b540cc0c0c0bd330c352331838`
- **`data/validated/aapl_validated_aapl_2015_2025_v1.csv`:**
  `72fe263b25d61bce1e5590f6fe053992b2a4696bdf46031282094ea87208b834`

---

## 8. Hướng dẫn sử dụng khi bàn giao và Tái lập quy trình

1. **Đối với thành viên nhận gói dữ liệu (TV2 và các thành viên khác):**
   - Giải nén và đặt trực tiếp thư mục `raw/`, `validated/`, `metadata/` cùng tệp `DATA_REPORT.md` vào bên trong thư mục `data/` tại gốc dự án (tránh tạo lồng thêm một cấp thư mục `data/data/`).
   - Đọc trực tiếp tệp đầu vào chuẩn tại `data/validated/aapl_validated_aapl_2015_2025_v1.csv` để tiến hành bước chia tập, fit `StandardScaler` trên tập Train và tạo cửa sổ trượt (`lookback = 30`, `forecast_length = 1` và `5`). Không tự ý tải lại dữ liệu từ Yahoo Finance để tránh làm sai lệch mã băm `dataset_version: aapl_2015_2025_v1`.
2. **Lệnh tái lập toàn bộ quy trình từ mã nguồn (khi cần kiểm tra độc lập):**
   ```bash
   python -m backend.data.acquisition.downloader
   python -m backend.data.validation.validator
   python -m unittest discover -s tests/data -v
   ```