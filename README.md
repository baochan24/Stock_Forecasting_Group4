# Stock Forecasting Group 4

## TV4 completed locally

The TV4 branch includes the training pipeline, required TV1-TV3 source dependencies, 69 passing training tests, official experiment configurations and an executed notebook. Start with [TV4 setup](docs/TV4_Setup_and_Reproduce.md) and [handoff instructions](docs/TV4_Handoff_TV5_TV6.md). [Training notebook](notebooks/04_TV4_Training_and_Experiments.ipynb) contains items 1-10. Raw data, scalers, checkpoints, generated logs, ZIPs and virtual environments are delivered separately through the local TV4 handoff package.


**LSTM-Based Stock Price Forecasting: A Case Study on AAPL**  
Dự báo giá cổ phiếu AAPL bằng mạng LSTM — coursework Deep Learning.

## Trạng thái hiện tại
Repository chứa **bộ khung và tài liệu Define/Design đã thống nhất**. Chưa có implementation chạy được, dataset đã tải, checkpoint đã train hoặc kết quả thực nghiệm. Các thư mục module hiện có README mô tả trách nhiệm, không phải code đã hoàn thành.

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
| tests/ | Vị trí kiểm tra có ý nghĩa theo module, chưa có test thực thi |
| scripts/, notebooks/ | Entry points và khảo sát/trình diễn sẽ triển khai |

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

Khi có release đầy đủ, thành viên dùng dataset/model/scaler/config đã bàn giao để chạy inference **không cần train lại**. Hiện chưa có release đó.

## Dữ liệu, logs và Git
.gitignore giữ hướng dẫn thư mục nhưng loại dữ liệu/checkpoint/logs sinh ra khỏi commit mặc định. Git chứa source/docs/config và các báo cáo có chủ đích. Kênh nhận artifacts sẽ được xác định trước bàn giao. Không đưa môi trường ảo hoặc thông tin bí mật lên Git.

## Sản phẩm coursework
Bảy mục báo cáo: vấn đề/phạm vi; dữ liệu mẫu/mô tả; mã nguồn; hướng dẫn cài đặt/chạy; demo hệ thống; so sánh baseline; phân tích lỗi/giới hạn. Các file reports hiện là khung, chưa có kết quả.

## Trình tự triển khai
Hoàn tất thiết kế → dữ liệu/baseline → LSTM một bước và đo CPU → khóa thực nghiệm → CNN/multi-step trên validation → test/phân tích → release → web tích hợp → kiểm tra máy khác/bàn giao. Web có thể làm song song bằng dữ liệu minh họa gắn nhãn; không dùng test để phát triển mô hình.
