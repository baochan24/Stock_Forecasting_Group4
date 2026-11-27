# Quy tắc làm việc — Stock Forecasting Group 4

Tài liệu này là bộ quy tắc bắt buộc cho mọi thành viên (TV1–TV6) và mọi công cụ AI hỗ trợ khi làm việc trong repository. Không ai được phép vi phạm các quy tắc dưới đây trừ khi toàn nhóm thống nhất sửa đổi và ghi vào Decision Log.

---

## 1. Cấu trúc và tổ chức

| Quy tắc | Mô tả |
|---|---|
| **Không thêm thư mục cấp cao mới** | Chỉ dùng các thư mục đã có: `backend/`, `frontend/`, `docs/`, `reports/`, `data/`, `experiments/`, `artifacts/`, `logs/`, `tests/`, `scripts/`, `notebooks/`. Cần thư mục mới phải thảo luận và ghi Decision Log. |
| **Không đổi tên, di chuyển hoặc xóa thư mục/file đã có** | Mọi thay đổi cấu trúc phải được nhóm trưởng (TV6) duyệt và cập nhật `FILE_STRUCTURE.md`. |
| **Thêm file đúng vị trí** | File code đặt trong module tương ứng của `backend/` hoặc `frontend/`. File tài liệu vào `docs/`. Báo cáo vào `reports/`. Test vào `tests/<module>/`. |
| **Giữ README module** | Không xóa hoặc ghi đè các `README.md` mô tả trách nhiệm module. Có thể bổ sung thông tin nhưng không thay đổi trách nhiệm đã chốt. |

## 2. Phạm vi dự án

| Quy tắc | Mô tả |
|---|---|
| **Chỉ AAPL, giá đóng cửa điều chỉnh, 2015–2025** | Không thêm mã cổ phiếu, loại giá hoặc khoảng thời gian khác nếu chưa thống nhất. |
| **Ba mô hình + baseline** | LSTM một bước, CNN 1D một bước, LSTM multi-step năm bước, persistence baseline. Không thêm mô hình khác (Transformer, GRU, XGBoost…) trừ khi nhóm đồng ý và ghi Decision Log. |
| **CPU only** | Không yêu cầu GPU. Code phải chạy được trên CPU. |
| **Không mở rộng phạm vi** | Không thêm tính năng đăng nhập, giao dịch, cập nhật real-time, notification, hoặc bất cứ gì ngoài Define/Design đã chốt. |

## 3. Dữ liệu và thực nghiệm

| Quy tắc | Mô tả |
|---|---|
| **Chia tập theo thời gian** | Train: 2015–2022, Validation: 2023, Test: 2024–2025. Không chia ngẫu nhiên. |
| **Scaler chỉ fit trên train** | `StandardScaler` fit một lần trên tập train. Không fit lại khi inference hoặc trên validation/test. |
| **Không dùng test để phát triển** | Test chỉ chạy sau khi chốt cấu hình bằng validation. Không chọn seed/hyperparameter dựa trên kết quả test. |
| **Đánh giá trên giá gốc** | MAE/RMSE tính trên thang USD gốc, sau inverse transform. Không đánh giá trên giá chuẩn hóa. |
| **Multi-step đánh giá từng bước** | Năm target của mỗi mẫu phải nằm cùng tập. Đánh giá riêng từng horizon step. |
| **Ba seed cho cấu hình cuối** | Ba seed định trước, báo cáo từng seed, trung bình và độ lệch chuẩn. Không chọn seed thắng test. |
| **Cùng tập mẫu khi so sánh** | Khi so sánh hai phương pháp, phải dùng cùng tập mẫu. Không bỏ mẫu thiếu mà không ghi rõ. |
| **Không đưa target vào inference** | Module inference không nhận giá mục tiêu. Target chỉ dùng cho training/evaluation. |

## 4. Git và quản lý file

| Quy tắc | Mô tả |
|---|---|
| **Tuân thủ .gitignore** | Không commit dataset, checkpoint, scaler, logs sinh ra, môi trường ảo hoặc thông tin bí mật. |
| **Git chứa source/docs/config** | Chỉ commit mã nguồn, tài liệu, cấu hình và báo cáo có chủ đích. |
| **Không ghi đè run cũ** | Mỗi run có ID duy nhất. Không xóa hoặc ghi đè kết quả của run trước. |
| **Ghi cách nhận artifacts khi bàn giao** | Clone repository không đủ — phải có hướng dẫn nhận dataset, checkpoint, scaler tương ứng. |

## 5. Ranh giới module và dependencies

| Quy tắc | Mô tả |
|---|---|
| **Front-end chỉ gọi API** | Không import trực tiếp logic backend trong frontend. |
| **Models/baselines/transforms không phụ thuộc training/API/front-end** | Các module này phải độc lập, có thể test riêng. |
| **API không gọi training** | Không có training endpoint. API chỉ phục vụ inference và đọc kết quả. |
| **Inference không cập nhật trọng số** | Module inference chỉ đọc checkpoint, không train hoặc fine-tune. |
| **Artifact Management không điều khiển training** | Chỉ lưu/nạp/kiểm tra, không quyết định khi nào train. |
| **Không nhân bản logic** | Metric tính ở `evaluation/`, không viết lại ở nơi khác. Persistence tính ở `baselines/`, không lặp lại ở inference. |

## 6. Phân công và phối hợp

| Quy tắc | Mô tả |
|---|---|
| **Làm đúng phần được giao** | TV1 dữ liệu, TV2 preprocessing, TV3 LSTM, TV4 training, TV5 CNN, TV6 baseline/evaluation/tích hợp/API/frontend. Xem chi tiết tại `docs/12_Team_Assignment.md`. |
| **API và front-end là việc của TV6** | TV1–TV5 không tự ý triển khai API hoặc giao diện. |
| **Thay đổi interface phải thống nhất** | Thay đổi shape, format dữ liệu hoặc hợp đồng giữa modules phải thông báo và đồng ý trước khi tích hợp. |
| **Không thay Define/Design đơn phương** | Mọi thay đổi thiết kế phải thống nhất nhóm và ghi vào `docs/11_Decision_Log.md`. |

## 7. Tài liệu và báo cáo

| Quy tắc | Mô tả |
|---|---|
| **Không điền kết quả trước khi chạy** | Chưa chạy phải ghi rõ "chưa kiểm chứng". Không bịa số liệu. |
| **Ghi logs, audit và bằng chứng** | Mọi run phải có cấu hình, seed, logs, kết quả. Audit ghi đạt/không đạt kèm bằng chứng. |
| **Phân biệt minh họa và kết quả thật** | Trace, ví dụ minh họa phải gắn nhãn rõ ràng, không trộn với kết quả thực nghiệm chính thức. |
| **Bảy mục báo cáo coursework** | Vấn đề/phạm vi, dữ liệu, mã nguồn, cài đặt/chạy, demo, so sánh baseline, phân tích lỗi. Mỗi mục có người chịu trách nhiệm. |

## 8. Quy tắc cho AI/công cụ hỗ trợ

| Quy tắc | Mô tả |
|---|---|
| **Không tự ý thay đổi cấu trúc** | AI chỉ thêm file vào đúng vị trí, không tạo thư mục cấp cao mới, không đổi tên hoặc di chuyển file/thư mục. |
| **Không mở rộng phạm vi** | Không đề xuất hoặc triển khai tính năng ngoài Define/Design đã chốt trừ khi người dùng yêu cầu rõ ràng. |
| **Tuân thủ ranh giới module** | Code sinh ra phải đặt đúng module, đúng trách nhiệm, đúng dependency direction. |
| **Không bịa dữ liệu hoặc kết quả** | Không tạo dữ liệu giả mạo mô phỏng kết quả thực nghiệm. Dữ liệu mẫu minh họa phải gắn nhãn rõ. |
| **Giữ nhất quán với tài liệu hiện có** | Mọi code/config phải tương thích với hợp đồng dữ liệu trong `docs/04_Data_Flow_and_Contracts.md` và API trong `docs/05_API_Contract.md`. |
| **Ghi thay đổi** | Thay đổi quan trọng phải gợi ý ghi vào Decision Log. |

## 9. Release và bàn giao

| Quy tắc | Mô tả |
|---|---|
| **Release liên kết đầy đủ** | Mỗi release phải có dataset, scaler, config, checkpoint, kết quả và audit tương thích. |
| **Chọn seed phục vụ trước test** | Không chọn seed thắng test để đưa vào release. |
| **Kiểm tra trên máy khác** | Ít nhất một thành viên khác phải chạy được release trước khi bàn giao. |
| **Web nạp release cụ thể** | Front-end gửi `release_id`, không tự chọn checkpoint mới nhất. |

## 10. Quy trình thay đổi quy tắc

1. Đề xuất thay đổi và lý do.
2. Thảo luận nhóm (ít nhất nhóm trưởng duyệt).
3. Ghi vào `docs/11_Decision_Log.md` với ngày, nội dung và lý do.
4. Cập nhật `rule.md` này.

---

> **Ghi chú**: File này là tài liệu tham chiếu nhanh tổng hợp các quy tắc từ Define/Design/Team Assignment. Nguồn gốc chi tiết nằm trong các tài liệu tại `docs/`. Khi có xung đột, ưu tiên tài liệu gốc và thảo luận nhóm.
