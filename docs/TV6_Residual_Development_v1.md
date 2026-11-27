# Thử nghiệm cải tiến biểu diễn giá v1 — 27/11/2026

Người dùng yêu cầu “tiến hành fix lại các điểm xem mô hình có cải thiện hơn k”, sau đề xuất dự báo thay đổi giá. Cho phép thử nghiệm biểu diễn/target mới; không thay protocol/model chính thức. Đây là phát triển sau khi đã quan sát test2024–2025, không được quảng bá như vòng đánh giá held-out độc lập mới.

## Contract phiên bản riêng

Forecast Input/Target gốc TV2 không đổi. Trong nhánh phát triển, với anchor=P(t), s là StandardScaler.scale_ fit **giá train của fold**:

- X_relative=(P(t−29:t)−P(t))/s; input cuối bằng0.
- y_delta=(P(t+1:t+H)−P(t))/s.
- Giá dự báo=P(t)+s*model(X_relative). H=1 hoặc5 trực tiếp từ cùng anchor, không cộng dồn recursive.
- Model nhận input relative CPUfloat64, trả delta chuẩn hóa; scaler.mean_ không tham gia delta. Anchor chỉ lấy từ input. Inference không nhận target.
- Khởi tạo head residual bằng0 để bắt đầu tại persistence; mô hình control giữ khởi tạo gốc. Đây là gói cải tiến gồm relative input, delta target và zero-head; không phải ablation tách tác động riêng từng yếu tố.
- Không thay kiến trúc core hoặc số tham số. Không đưa checkpoint này vào FrozenForecaster/release v1.

## Kế hoạch khóa trước chạy

`experiments/configs/tv6_residual_development_v1.json`:2 folds,36 runs=(2 năm validation2022/2023)×(3 tasks LSTMh1/CNNh1/LSTMh5)×(2 biểu diễn)×(3 seeds42/123/456). Train của fold đến31/12 năm trước; mọi target của window phải cùng phạm vi train/validation. Scaler fold2022 chỉ fit2015–2021, fold2023 chỉ fit2015–2022. Dùng input/target train/val đã pin của TV2, không sinh pipeline cleaning/windowing song song. Không đọc test targetJSON/NPZ hoặc chạy testforward.

Mỗi run Adam/MSE,lr0.001,batch32,max100epoch,patience10,best theo validationMSE. Equal maximum budget cho control/residual; ghi actualepochs/thời gian. Không bỏ seed hoặc đổi hyperparameter theo kết quả. Persistence dùng cùng actual/mẫu. Metrics USD từngseed/perhorizon/overall,mean/std mẫu. H5overall flatten trướcRMSE.

Sampler trong CLI mới shuffle minibatch **chỉ bên trong tập train**, cùng generator seed cho control/residual; validation giữ thứ tự. Đây không phải random split: target train/validation và scaler vẫn tách theo thời gian, model LSTM reset state mỗi window. Runner v1 cũ dùng shuffle=False và một bước common60; vì vậy control mới là đối chứng ghép cặp cho thử nghiệm, không là tái lập điểm v1 hoặc ablation chỉ đổi duy nhất target so với v1. Mã runner và plan được hash trước chạy; không đổi sampler giữa chừng.

Đánh giá2022/2023 đều là development (2023 từng được dùng trước); kết quả tích cực không chứng minh hiệu quả trên dữ liệu tương lai chưa thấy. Test cũ giữ nguyên. Muốn phát hành phiên bản mới cần audit integration/contract/checkpoint và protocol tiếp theo; không tự động thay model từ kết quả thử nghiệm.

CLI `.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_residual_development.py`. Save scaler/checkpoint mới theo timestamp,manifest ghi representation,purpose=post-test-development-not-release,hash/config/fold/bestepoch. Dùng training loop TV4, quản lýseed và metric có sẵn. NotebookTV6 sẽ đọc kết quả thật, không kích hoạt train lại khi Run All.
