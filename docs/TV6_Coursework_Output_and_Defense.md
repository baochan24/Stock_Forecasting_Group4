# Chốt đầu ra coursework và cách trình bày

Đối chiếu đề gốc Topic4 và mẫu đăng ký ngày28/11/2026. Kết luận kỹ thuật: đã xây dựng pipeline và demo local giải bài toán dự báo giá phiên tiếp theo bằng LSTM, cùng hai phần mở rộng. Không đồng nhất hoàn thành implementation với chứng minh LSTM vượt baseline hoặc nghiệm thu bàn giao trên máy khác.

Lượt hoàn thiện sau mục10 đã kiểm cài mới85 pins,62 tests API/handoff và14 kiểm tra Chrome/5 tests JavaScript bằng venv riêng. [Bằng chứng bàn giao](../reports/audits/TV6_Closure_and_Handoff.md). Venv mới vẫn cùng máy; không tự chuyển điều kiện máy thành viên khác sang đạt.

## Đề yêu cầu gì và sản phẩm trả ra gì?

| Nội dung đề | Đầu ra của nhóm | Nơi kiểm chứng |
|---|---|---|
| Yahoo Finance, chuỗi dữ liệu quá khứ | Snapshot AAPL adjusted close2015–2025,2766 phiên, nguồn/hash/quality và cửa sổ30 phiên | Notebook01/02; reports02; audit dữ liệu |
| LSTM regression dự báo phiên tiếp theo | Model H1, checkpoint/scaler/config/seed và giá dự báo USD cho T+1 | backend/models/lstm_one_step; API predictions; frontend Dự báo |
| Multi-step extension | LSTM direct5 outputs, ngày T+1..T+5 theo phiên dataset | backend/models/lstm_multi_step; metric per-horizon/overall; frontend5phiên |
| CNN vs.LSTM extension | CNN1D H1, cùng cohort và metric USD; cả3seed | backend/models/cnn_one_step; reports06; frontend So sánh |
| Đánh giá bài toán | MAE/RMSE, persistence, counts, mean/std mẫu3seed, phân tích lỗi | reports06/07; notebook06 |
| Sản phẩm chạy được | API12route, frontend AAPL Forecast Lab, hướng dẫn và gói web local có checksum | reports04/05; docs/TV6_Member_Setup_and_Run.md |

Đầu ra một request không chỉ là một con số: có release/dataset,origin,target dates,method,seed/run,horizon và predicted_price USD. Actual và error được ghép riêng sau inference. H1 có1 giá/phương pháp; H5 có5 giá/phương pháp, không hỗ trợ CNN H5. Không yêu cầu người xem train lại.

## Đủ10 nội dung đăng ký chưa?

| Mục đăng ký | Nội dung đã xác định | Trạng thái |
|---|---|---|
| Tên đề tài | LSTM-Based Stock Price Forecasting: A Case Study on AAPL | Có |
| Hướng chính | AI dự đoán, regression | Có |
| Người dùng/vấn đề | Giảng viên, người học và nhóm thực nghiệm; kiểm chứng dự báo từ lịch sử | Có |
| Mục tiêu đo lường | ForecastH1/H5,MAE/RMSE USD,cùng mẫu,3seed; không ngưỡng bắt buộc LSTM thắng | Có kết quả thật |
| Dữ liệu | Yahoo/AAPL/adjusted close/2766 phiên; nguồn và hash | Kỹ thuật có; quyền phân phối còn mở |
| Phạm vi | LSTM H1,H5,CNN H1,persistence,API/UI lịch sử | Có local |
| Phương pháp/baseline | Split theo target,scaler train,shared loop,validation selection,persistence | Có bằng chứng |
| Sản phẩm | Source,model/artifacts,API,UI,notebooks,báo cáo/hướng dẫn | Có local; gói cuối kiểm cùng máy |
| Đánh giá | Original locked test tách residual post-development; lỗi/giới hạn | Có,không holdout mới |
| Kế hoạch/rủi ro | Phân công TV1–TV6 và các mốc thực tế trong audit | Có; deadline/hình thức nộp chờ xác nhận |

## Bảy phần báo cáo để nộp

Bảng kết quả đã xuất riêng để kiểm tra từng seed/horizon và đưa vào báo cáo:

- [So sánh H1/H5 overall](../reports/tables/TV6_Final_Comparison.csv).
- [Chi tiết từng horizon](../reports/tables/TV6_Final_Per_Horizon.csv).
- [Kết quả từng seed](../reports/tables/TV6_Final_Per_Seed.csv).
- [Hash nguồn và bảng xuất](../reports/tables/TV6_Final_Tables_Provenance.json).

Các bảng giữ nguyên giai đoạn original locked test và residual post-development old test. Không gộp hai giai đoạn thành một kết quả độc lập.

1. [Vấn đề và phạm vi](../reports/01_Problem_and_Scope.md).
2. [Dữ liệu mẫu và mô tả](../reports/02_Data_Description.md).
3. [Mã nguồn và triển khai](../reports/03_Implementation.md).
4. [Cài đặt và chạy](../reports/04_Setup_and_Run.md).
5. [Demo hệ thống](../reports/05_System_Demonstration.md).
6. [So sánh baseline và model](../reports/06_Baseline_and_Model_Comparison.md).
7. [Phân tích lỗi và giới hạn](../reports/07_Error_Analysis_and_Limitations.md).

Các mục là nội dung báo cáo kỹ thuật, chưa tự thay thế biểu mẫu/slide hoặc yêu cầu định dạng nộp riêng từ giảng viên.

## Chốt kết luận khoa học khi bảo vệ

“Nhóm đã triển khai LSTM dự báo adjusted close AAPL phiên tiếp theo, mở rộng5phiên và so sánh CNN trên cùng pipeline. Model gốc được đánh giá theo protocol khóa và thua persistence. Phân tích lỗi dẫn đến biểu diễn residual; bản này cải thiện rõ so với LSTM gốc và chỉ nhỉnh nhẹ persistence trên test cũ đã quan sát. Vì vậy chưa khẳng định ưu thế độc lập hoặc bền vững. Đóng góp của đồ án là pipeline có kiểm chứng, thực nghiệm minh bạch và hệ thống demo tái lập.”

Không nói LSTM luôn dự báo đúng,đã giải được quy luật giá,đạt accuracy phần trăm cho regression,hoặc có lợi nhuận. Không giấu kết quả model gốc hay gộp residual với original test thành một lần đánh giá độc lập.

## Việc còn cần xác nhận để nghiệm thu toàn bộ

- Thành viên khác cài môi trường và chạy gói bàn giao, gửi bằng chứng: chưa có. Đã có [hướng dẫn và mẫu biên bản](TV6_Member_Acceptance.md); người nhận chạy verifier với `--output` để lưu JSON. Nguồn giải nén/tiến trình riêng cùng máy không tương đương máy khác.
- Quyền phân phối dữ liệu và phương án nguồn thay thế được chấp thuận: [trạng thái hiện tại](TV6_Data_Use_and_Limits.md).
- Định dạng nộp,slide,deadline và xác nhận thành viên/giảng viên: chưa tự đặt hoặc giả định.

Không cần train thêm để làm audit/bàn giao này. Không cần thêm live data hoặc giao dịch để hoàn thành phạm vi đề Topic4.
