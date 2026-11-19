# Stock Forecasting Group 4

**LSTM-Based Stock Price Forecasting: A Case Study on AAPL**  
Dự báo giá cổ phiếu AAPL bằng mạng LSTM — coursework Deep Learning.

## Trạng thái hiện tại
Nhánh `Tâm` có **implementation dữ liệu TV1**: tải snapshot AAPL, kiểm tra metadata/chất lượng/lịch phiên, bảng validated bốn cột, notebook EDA/điều tra và 34 tests. Snapshot hiện tại có 2.766 phiên; đã kiểm chứng trong môi trường sạch trên cùng máy. Xác nhận người nhận/máy thành viên khác còn chờ. Đây chưa phải hệ thống model/train/API/web hoàn chỉnh; phần TV2 trở đi chưa được nghiệm thu trong phần việc này. Chưa tự merge nhánh này vào `main`.

## Bài toán và phạm vi
- Nguồn: Yahoo Finance, thu thập bằng yfinance; một mã **AAPL**, dữ liệu ngày **2015–2025**.
- Đặc trưng/mục tiêu: giá đóng cửa đã điều chỉnh, đơn vị USD. Ghi rõ chính sách điều chỉnh và giới hạn hồi cứu sau khi tải.
- Input chính: **30 phiên** đã biết; mục tiêu chính: giá phiên giao dịch tiếp theo.
- Baseline **persistence**: dự báo bằng giá gần nhất.
- Mô hình: **LSTM một bước**, **CNN 1D một bước** để so sánh, **LSTM direct multi-output năm bước**.
- Python/PyTorch, **CPU**. Công nghệ API/front-end chưa chọn.
- Sản phẩm cuối: hệ thống web phục vụ inference, đối chiếu và tương tác tìm hiểu mô hình; training chạy riêng.

Không đặt trước điều kiện LSTM phải thắng baseline; kết luận dựa trên thực nghiệm.

## Quy tắc thực nghiệm
| Tập | Ngày target | Vai trò |
|---|---|---|
| Train | 2015–2022, sau khi đủ lịch sử | Học trọng số và fit scaler |
| Validation | 2023 | Chọn cấu hình/checkpoint |
| Test | 2024–2025 | Đánh giá cuối |

- Không chia ngẫu nhiên theo thời gian; không đưa target vào inference.
- StandardScaler chỉ fit train; đánh giá MAE/RMSE trên thang giá gốc.
- Multi-step đánh giá riêng từng bước; toàn bộ năm target của mẫu nằm trong cùng tập.
- Checkpoint chọn theo validation; ba seed định trước cho cấu hình cuối, không chọn seed thắng test.
- Giữ dữ liệu/config/scaler/checkpoint/results tương thích qua release_id.

## Cấu trúc làm việc
| Thư mục | Trách nhiệm |
|---|---|
| backend/ | Data, models, baselines, training, inference, evaluation, artifacts, audit và API |
| frontend/ | Các vùng chức năng giao diện; framework còn mở |
| docs/ | Define, Design, API, risks, milestones và phân công |
| reports/ | Khung đủ bảy mục coursework, hình/bảng và bằng chứng audit |
| data/ | Snapshot, dữ liệu hợp lệ/chuẩn bị và metadata |
| experiments/ | Cấu hình và logs/kết quả từng run |
| artifacts/ | Scaler, checkpoint và release |
| logs/ | Logs web/audit vận hành |
| tests/ | Có suite TV1 dữ liệu; các phần model/train/API triển khai riêng |
| scripts/, notebooks/ | Entry points TV1, notebook có output và bằng chứng tái lập |

Xem [FILE_STRUCTURE.md](FILE_STRUCTURE.md) để biết danh sách file.

## Tài liệu bắt đầu
1. [Project Description và nền tảng](docs/01_Project_Description_and_Foundation.md)
2. [System Architecture](docs/02_System_Architecture.md)
3. [Ranh giới module](docs/03_Module_Boundaries.md)
4. [Data Flow](docs/04_Data_Flow_and_Contracts.md)
5. [API](docs/05_API_Contract.md)
6. [Technical Risks](docs/06_Technical_Risks.md) và [Milestones](docs/07_Milestones.md)
7. [Tái lập/phát hành](docs/08_Reproducibility_and_Release.md)
8. [Phân công sáu thành viên](docs/12_Team_Assignment.md)

## Phân công
TV1 dữ liệu; TV2 preprocessing/windowing; TV3 LSTM/trace; TV4 training LSTM; TV5 CNN và thực nghiệm; TV6 baseline/đánh giá/tích hợp. **API và front-end do TV6 — nhóm trưởng phụ trách riêng.** Chi tiết bàn giao và phối hợp ở tài liệu phân công; chưa gắn tên cá nhân.

## Cài đặt và chạy
Hiện chưa có lệnh train/API/front-end đã kiểm chứng vì implementation và dependencies chưa có. Theo dõi [hướng dẫn cài đặt/chạy](docs/09_Setup_and_Run.md) và [chi tiết còn mở](docs/10_Open_Decisions.md). Không suy luận rằng clone repository là có thể mở web ngay.

Phần TV1 đã có [hướng dẫn cài đặt và tái lập](docs/TV1_Setup_and_Reproduce.md), [notebook kết quả](notebooks/01_AAPL_Data_Exploration.ipynb) và bộ dependencies ghim. Nhận source/dataset đúng version từ các link trong hướng dẫn; không tải lại Yahoo để thay snapshot đã bàn giao.

Khi có release đầy đủ, thành viên dùng dataset/model/scaler/config đã bàn giao để chạy inference **không cần train lại**. Hiện chưa có release đó.

## Dữ liệu, logs và Git
.gitignore giữ hướng dẫn thư mục nhưng loại dữ liệu/checkpoint/logs sinh ra khỏi commit mặc định. Git chứa source/docs/config và báo cáo có chủ đích. Kênh bàn giao TV1 là Drive Project_CW trong hướng dẫn; model release chưa có. Không đưa môi trường ảo hoặc thông tin bí mật lên Git.

## Sản phẩm coursework
Bảy mục báo cáo: vấn đề/phạm vi; dữ liệu mẫu/mô tả; mã nguồn; hướng dẫn cài đặt/chạy; demo hệ thống; so sánh baseline; phân tích lỗi/giới hạn. Phần TV1 có số liệu/bằng chứng thực tế; các kết quả model/demo/so sánh chưa được tạo trong phần việc này.

## Trình tự triển khai
Hoàn tất thiết kế → dữ liệu/baseline → LSTM một bước và đo CPU → khóa thực nghiệm → CNN/multi-step trên validation → test/phân tích → release → web tích hợp → kiểm tra máy khác/bàn giao. Web có thể làm song song bằng dữ liệu minh họa gắn nhãn; không dùng test để phát triển mô hình.
