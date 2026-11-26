# Project Description và nền tảng thiết kế

Phiên bản: 1.0 — 05/11/2026

Trạng thái: tổng hợp các quyết định thiết kế đã thống nhất. Chưa có dữ liệu tải về, code hoặc kết quả thực nghiệm được kiểm chứng trong quá trình xây nền này. Các cấu hình là điểm khởi đầu, không phải cấu hình tối ưu đã được chứng minh.

## Phần 1. Project Description

### Đối chiếu đề gốc — 21/11/2026

Đã đọc trực tiếp `docs/đề_yêu_cầu.md` và `docs/yêu_cầu_mẫu_đề_tài.md` sau khi người dùng lưu nội dung. Topic 4 xác định regression, Yahoo Finance, LSTM dự báo giá phiên tiếp theo từ chuỗi quá khứ; phần mở rộng là multi-step và CNN vs. LSTM. Thiết kế hiện tại phù hợp hướng này. AAPL, adjusted close, 2015–2025, CPU, lookback 30, split năm, StandardScaler, persistence và direct 5 bước là lựa chọn cụ thể của nhóm, không phải thông số đề gốc ghi bắt buộc.

Mẫu đăng ký yêu cầu 10 nội dung: tên đề tài, hướng chính, người dùng/vấn đề, mục tiêu đo lường, dữ liệu, phạm vi, phương pháp, sản phẩm, đánh giá, kế hoạch/rủi ro. Hướng chính của đề tài này là AI dự đoán. Bảy nhóm báo cáo gồm vấn đề/phạm vi; dữ liệu mẫu/mô tả; source; cài đặt/chạy; demo; so sánh baseline; phân tích lỗi/giới hạn — khớp cấu trúc reports hiện có. Khớp cấu trúc không có nghĩa các báo cáo đã hoàn thành.

Các điểm còn cần hoàn thiện khi tổng hợp đăng ký/bàn giao: bằng chứng và giới hạn quyền sử dụng/phân phối dữ liệu Yahoo Finance; phương án dự phòng khi nguồn tải không khả dụng (snapshot cố định hỗ trợ tái lập nhưng chưa tự là nguồn thay thế được phê duyệt); mốc hoàn thành thực tế và rủi ro/phụ thuộc tương ứng. Không tự thay nguồn hoặc gán quyền sử dụng khi chưa xác minh. Các việc này không làm thay đổi flow TV2 đang thực hiện. Các trạng thái dựng nền trong bản 1.0 bên dưới là lịch sử; xem audit mới nhất để biết tiến độ code/dữ liệu.

### 1. Project name

**LSTM-Based Stock Price Forecasting: A Case Study on AAPL**

**Dự báo giá cổ phiếu AAPL bằng mạng LSTM.**

Sản phẩm là hệ thống web phục vụ thực nghiệm, demo và tương tác tìm hiểu Deep Learning. Trọng tâm đầu tư là dữ liệu, huấn luyện, đánh giá và giải thích quy trình mô hình. CNN 1D và multi-step là các phần mở rộng theo Topic 4.

### 2. Problem

Nghiên cứu sử dụng chuỗi 30 phiên giá đóng cửa đã điều chỉnh của AAPL để dự báo giá cùng loại ở phiên giao dịch tiếp theo. Tại cuối phiên t, input là [P(t−29), …, P(t)] và target là P(t+1).

Câu hỏi chính: LSTM có giảm sai số dự báo so với persistence — dự báo giá phiên tiếp theo bằng giá phiên gần nhất — trong phạm vi dữ liệu và thực nghiệm được chọn hay không?

Không đặt điều kiện LSTM phải thắng. Kết luận phải dựa trên số liệu; biểu đồ bám sát giá không tự chứng minh mô hình hiệu quả. Kết quả trên AAPL và giai đoạn đã chọn không tự suy rộng sang cổ phiếu khác, tương lai hoặc lợi nhuận giao dịch.

### 3. Target users and uses

- Thành viên nhóm: chạy, kiểm tra và truy vết thực nghiệm.
- Giảng viên và người học: quan sát demo, hiểu dữ liệu đi qua mô hình và đối chiếu kết quả.
- Trải nghiệm chính: chọn thời điểm lịch sử hợp lệ, xem input, chạy inference từ mô hình đã train, đối chiếu baseline và thực tế.
- Không bắt buộc train lại để mở web. Dự báo từ dữ liệu cập nhật mới nhất để phát triển sau; chưa thuộc phạm vi chính.

### 4. Input and output

| Thành phần | Đầu vào | Đầu ra |
|---|---|---|
| Thu thập | AAPL, dữ liệu ngày, 2015–2025, chính sách điều chỉnh rõ ràng | Bản dữ liệu cố định và thông tin nguồn gốc |
| LSTM một bước | B cửa sổ, shape (B,30,1), đã chuẩn hóa | (B,1), sau đó inverse transform thành giá |
| Persistence một bước | Giá cuối mỗi cửa sổ | Cùng giá đó cho phiên tiếp theo |
| CNN một bước | Cùng lịch sử; đổi thứ tự chiều theo yêu cầu lớp CNN | Một giá phiên tiếp theo cho mỗi mẫu |
| LSTM multi-step | (B,30,1) | (B,5): năm giá tương lai dự báo đồng thời |
| Persistence multi-step | Giá gần nhất P(t) | [P(t),P(t),P(t),P(t),P(t)] |

Hai dự báo LSTM và persistence là kết quả của hai phương pháp độc lập, không phải hai đầu ra của LSTM một bước. Giá thực tế là target đối chiếu, không phải input tương lai.

Mỗi kết quả cần có thời điểm dự báo, ngày target, phương pháp, horizon, run ID, loại giá và đơn vị USD. Sai số chỉ hiển thị khi có thực tế.

### 5. Core features

1. Thu thập, kiểm tra, mô tả và lưu dữ liệu chung.
2. Chia dữ liệu theo thời gian, chuẩn hóa và tạo cửa sổ có kiểm tra rò rỉ.
3. Huấn luyện LSTM, lưu checkpoint và logs.
4. Tính persistence; huấn luyện CNN 1D để so sánh một bước.
5. Huấn luyện LSTM direct multi-output cho năm phiên.
6. Đánh giá, phân tích lỗi và ghi giới hạn.
7. Web tương tác: xem lịch sử, dự báo, kết quả so sánh và quy trình tính toán.
8. Truy vết dữ liệu, cấu hình, mô hình và kết quả; hướng dẫn chạy trên máy khác.

### 6. Technology constraints

- Python và PyTorch; huấn luyện và inference trên CPU, không yêu cầu GPU.
- Yahoo Finance qua yfinance; một mã AAPL, dữ liệu ngày 01/01/2015–31/12/2025. Số phiên thực tế cần xác minh sau tải.
- Một đặc trưng giá đóng cửa đã điều chỉnh. Ghi rõ chính sách tải, thời điểm tải và giới hạn của dữ liệu điều chỉnh hồi cứu; không mô tả đây là backtest point-in-time hoàn hảo.
- StandardScaler fit trên chuỗi giá train, dùng lại cho các tập khác.
- Tách huấn luyện khỏi web inference. Web không tự train khi người dùng bấm dự báo.
- Công nghệ web/API, kiến trúc CNN chi tiết và hình thức triển khai chưa được chọn.

### 7. Evaluation criteria

- Tính đúng: dữ liệu, thứ tự thời gian, input–target, scaler và checkpoint phù hợp.
- Chất lượng: MAE, RMSE trên giá gốc, cùng ngày target giữa các phương pháp.
- Multi-step: MAE/RMSE riêng cho bước 1–5; không chỉ dùng một số tổng.
- Ổn định thực nghiệm: ba seed định trước cho cấu hình cuối; công bố từng seed, trung bình và độ lệch chuẩn với quy ước rõ ràng.
- Tài nguyên: số tham số, thời gian train và inference được đo riêng trong điều kiện ghi nhận.
- Tái lập: nạp lại mô hình, tính lại metric và chạy hướng dẫn trên máy thành viên khác.
- Sản phẩm: đủ vấn đề/phạm vi, dữ liệu mẫu/mô tả, mã nguồn, hướng dẫn cài đặt/chạy, demo, so sánh baseline, phân tích lỗi/giới hạn.
- Không có ngưỡng accuracy đặt trước hoặc điều kiện LSTM bắt buộc thắng. Chưa đặt mức cải thiện tối thiểu khi chưa có căn cứ.

## Phần 2. Nền thực nghiệm đã thống nhất

### 8. Chia dữ liệu và tạo mẫu

| Tập | Khoảng ngày target | Vai trò |
|---|---|---|
| Train | 2015–2022, sau khi đủ lịch sử | Học trọng số |
| Validation | 2023 | Chọn cấu hình/checkpoint |
| Test | 2024–2025 | Đánh giá cuối |

- Không chia ngẫu nhiên. Input có thể lấy lịch sử từ tập đứng trước nếu đã có trước target.
- Không đảo thứ tự bên trong cửa sổ. Có thể shuffle các cửa sổ train độc lập; validation/test giữ thứ tự.
- Không tự thêm ngày nghỉ thành phiên giao dịch. Xử lý thiếu/trùng phải ghi lý do, không dùng tương lai điền quá khứ.
- Hidden/cell state khởi tạo 0 cho mỗi cửa sổ; không truyền trạng thái giữa các mẫu.
- Với một bước, cập nhật input bằng giá thực tế đã xuất hiện khi chuyển thời điểm dự báo; giữ nguyên trọng số.
- Với năm bước, cả năm target phải nằm trong cùng tập. Ghi số mẫu không đủ điều kiện, gồm mẫu vượt ranh giới hoặc hết lịch sử tương lai.
- Khi so sánh lookback khác nhau, dùng giao các ngày target hợp lệ.

### 9. Huấn luyện một bước

Cấu hình khởi đầu: lookback 30, một lớp LSTM, hidden size 32, Linear ra 1; batch 32; Adam, learning rate 0.001; MSE; tối đa 100 epoch; early stopping patience 10.

Một batch: bật train mode → chuẩn bị tensor đúng shape/dtype/device → xóa gradient → khởi tạo trạng thái → forward → MSE → backward → optimizer step → ghi nhận. Giữ batch cuối. Epoch loss là tổng batch loss nhân số mẫu chia tổng số mẫu.

Sau mỗi epoch: eval mode và tắt gradient → validation → tổng hợp loss → lưu checkpoint nếu validation MSE thấp hơn → cập nhật early stopping. Kết thúc nạp lại checkpoint tốt nhất, không mặc định dùng epoch cuối.

Kiểm tra số hữu hạn; khi NaN/Inf xuất hiện phải ghi lỗi và dừng xử lý nguyên nhân. Gradient clipping chưa chốt; nếu bổ sung cần ngưỡng và ghi cấu hình.

Lookback 10/30/60 là thí nghiệm có kế hoạch nhưng số lần chạy cuối cần giới hạn sau khi đo CPU. Không chọn seed hoặc cấu hình bằng test.

### 10. CNN vs. LSTM

So sánh ban đầu tại lookback 30, cùng dữ liệu, target, scaler và quy tắc đánh giá. Chọn hai mạng nhỏ; ghi số tham số. Cùng optimizer/loss khởi đầu không tự bảo đảm công bằng: nếu tuning, cần ngân sách tương đương và quy tắc validation chung. Thời gian train/inference đo riêng trên cùng máy.

Kiến trúc CNN và ngân sách thử chưa định nghĩa. Không mặc định CNN nhanh hơn hoặc LSTM tốt hơn. Thí nghiệm LSTM dự báo thay đổi giá là tùy chọn ưu tiên sau các yêu cầu chính và mở rộng trong đề.

### 11. Multi-step direct multi-output

Input 30 phiên → LSTM hidden 32 → Linear ra 5. Huấn luyện riêng từ đầu, checkpoint riêng; tái sử dụng thành phần pipeline. MSE trung bình các mẫu và năm bước, trọng số bước bằng nhau. Chọn checkpoint bằng validation MSE tổng; theo dõi thêm từng bước.

Không dùng giá thực tế tương lai trong cùng lần dự báo năm bước. Đánh giá trên cùng cặp thời điểm dự báo–bước–ngày target với persistence. Các cửa sổ có thể chồng lấp; cùng một ngày target có thể xuất hiện ở horizon khác nhau, nên không ghép chỉ theo ngày hoặc coi mọi dự báo là quan sát độc lập.

### 12. Đánh giá và phân tích lỗi

Inverse transform: P_hat = z_hat × sigma_train + mu_train. Đối chiếu target khôi phục với dữ liệu gốc theo dung sai số học cần xác định khi triển khai.

Sai số e = dự báo − thực tế; MAE = mean(abs(e)); RMSE = sqrt(mean(e²)). Tính từ toàn bộ mẫu, không trung bình RMSE batch. Không làm tròn trước khi tính metric.

Khóa kết quả gồm run ID, phương pháp, thời điểm dự báo, horizon và ngày target. Kiểm tra đủ mẫu, không trùng khóa, đúng scaler/checkpoint và không âm thầm loại sai số lớn.

Phân tích dự kiến: sai số có dấu, sai số tuyệt đối, chênh lệch sai số tuyệt đối persistence–LSTM, theo giai đoạn định trước và các trường hợp tốt/kém theo quy tắc chọn rõ ràng. Ghi số mẫu, dung sai hòa và số trường hợp được chọn. Trung bình sai số có dấu có thể triệt tiêu nên xem cùng MAE.

Không suy nguyên nhân từ biểu đồ hoặc hidden state. Phân nhóm dùng biến động target là phân tích hồi cứu, không phải thông tin input. Trung bình metric các seed không phải ensemble. Nếu xem test rồi sửa mô hình, phải ghi rõ ảnh hưởng đến tính độc lập của đánh giá.

### 13. Logs, audit và bàn giao

Mỗi run lưu: phiên bản/hash dữ liệu, chính sách tải, cấu hình, seed, môi trường, Git commit và trạng thái thay đổi chưa commit nếu có, scaler, epoch logs, checkpoint, dự báo, metric và audit.

Logs ghi điều đã xảy ra. Audit ghi quy tắc, kết quả đạt/không đạt, bằng chứng và lỗi. Lưu các bản truy vết đại diện để tìm hiểu phép tính; không lưu mọi tensor ở mọi batch.

Phiên bản demo cố định liên kết dữ liệu, checkpoint, scaler, cấu hình và kết quả; không bị run mới ghi đè. Thành viên khác không phải train lại để dùng demo. Khả năng chạy máy khác cần được kiểm tra thực tế. Seed không bảo đảm giống tuyệt đối giữa mọi máy.

Ưu tiên nạp inference và chạy lại từ đầu. Resume giữa chừng chưa thuộc mức tối thiểu; nếu triển khai phải lưu optimizer, epoch, early stopping và trạng thái ngẫu nhiên phù hợp.

### 14. Hệ thống web và tương tác tìm hiểu

Luồng: chọn chế độ/ngày → kiểm tra yêu cầu → lấy lịch sử → chuẩn hóa → inference → inverse transform → tính baseline → đối chiếu nếu có target → trả kết quả có mã phiên bản → hiển thị.

Một bước có persistence, LSTM, CNN; năm bước có persistence và LSTM. Metric toàn tập lấy từ kết quả kiểm tra đã lưu; metric khoảng ngày được chọn phải gắn nhãn riêng và dùng cùng quy tắc back-end. Phân biệt kết quả lưu sẵn với inference mới, không trộn phiên bản.

Nội dung tìm hiểu: input/target, shape, chuẩn hóa, LSTM và Linear, loss, checkpoint. Hidden/cell state hoặc gate thật chỉ hiển thị sau khi cơ chế truy vết được đối chiếu với mô hình chính. Minh họa phải gắn nhãn; không gán ý nghĩa chưa chứng minh cho chiều hidden.

Front-end đề xuất tên: Giá dự báo — LSTM; Giá tham chiếu — Giữ nguyên giá phiên trước (Persistence); Giá thực tế. Thiếu dữ liệu hoặc không nạp được mô hình phải báo lỗi, không tạo số giả thay thế.

## Phần 3. Ghép pipeline và các việc còn mở

### 15. Hai luồng liên kết

**Luồng nghiên cứu:** thu thập và đóng phiên bản dữ liệu → audit dữ liệu → chia tập/fit scaler/tạo mẫu → persistence → train và validation → chọn cấu hình/checkpoint → khóa lựa chọn → test → phân tích lỗi → đóng phiên bản phát hành.

**Luồng sử dụng web:** yêu cầu người dùng → kiểm tra → nạp bộ mô hình/scaler/cấu hình tương ứng → chuẩn bị input → inference và baseline → kết quả/giải thích/truy vết → front-end.

### 16. Việc chưa chốt hoặc chưa kiểm chứng

| Nội dung | Trạng thái |
|---|---|
| Dữ liệu thực tế, số mẫu, thiếu/trùng, chính sách tải cụ thể | Cần tải và audit |
| Framework web/API và triển khai | Cần chọn ở bước thiết kế hệ thống |
| CNN cụ thể, ngân sách tuning, danh sách seed | Cần đặc tả trước thực nghiệm |
| Dung sai số học, quy ước độ lệch chuẩn, lựa chọn ví dụ lỗi | Cần đặc tả trước kiểm tra/đánh giá |
| Truy vết trạng thái/gate và batch minh họa | Cần triển khai và đối chiếu |
| Thời gian CPU, RAM, tái lập máy khác | Cần đo |
| LSTM/CNN có vượt baseline không | Chưa có kết quả |
| Đăng nhập, giao dịch, cập nhật giá trực tiếp | Chưa được đưa vào phạm vi chính |

### 17. Điều kiện chuyển sang cấu trúc code

Tài liệu này là mốc tham chiếu thiết kế đã tổng hợp, không phải chứng nhận hệ thống hoạt động đúng. Bước tiếp theo là đặc tả module, dữ liệu trao đổi và thứ tự triển khai; chốt các chi tiết cần thiết trước từng thực nghiệm. Mọi thay đổi phải ghi lý do và ảnh hưởng, không coi mọi cấu hình ban đầu là bất biến.

Đối chiếu source: Topic 4 — Yahoo Finance, LSTM regression, next-day forecasting; extensions multi-step và CNN vs. LSTM. Sản phẩm báo cáo bao phủ đủ bảy mục trong Các-yêu-cầu-của-course-work.txt. Đây là nội dung mô tả phương án, không phải báo cáo kết quả đã thực hiện.
