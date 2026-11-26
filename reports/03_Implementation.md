# Mã nguồn và triển khai

## TV4 — contract CPU float64, mục2 (25/11/2026)

Training loop đã bỏ downcastfloat32, giữ đúng dtype input/target và kiểm khớp parameters CPU. Hai LSTM TV3 bắt buộc float64, một feature, target horizon1/5; không thay model hoặc global dtype.52/52 tests và notebook04 có6/6 code cells đạt, bao gồm Adam/validation thực trên tensors tổng hợp, batch cuốiB1, no implicit cast và shape/device guards. Chi tiết logs/protected hashes: reports/audits/TV4_Progress.md. Dữ liệu AAPL/factories và checkpoint thật vẫn chờ mục3/5. Mô tả baseline mục1 bên dưới là trạng thái trước cập nhật này.

## TV4 — tiếp nhận nền training, mục1 (25/11/2026)

Đã nhận9 source/config/test files từ PR#10 commit16555929210314b1eb06da9dc84b827ececc1b9e; đặt experiment_runner.py đúng backend/experiments/runner. Nội dung source giữ nguyên. Venv TV4 riêng có69 dependency pins gồm PyYAML;16/16 tests baseline trực tiếp workspace và5/5 code cells notebook04 đạt. Bằng chứng ở reports/audits/TV4_Progress.md.

Đây chưa là nghiệm thu huấn luyện AAPL: cast float32 còn mục2, factories/version/scaler thật mục3, checkpoint hook thật mục5. Tests dùng tensors tổng hợp và mock checkpoint; không có metric dự báo hoặc official trained checkpoint TV4 trong mục1.

## TV3 — kiến trúc, trace và bàn giao kỹ thuật local

LSTM1 lớp, input_size1/hidden32, batch_first, h/c zero mới mỗi forward. Lấy hidden time step cuối qua Linear1 hoặc5;4513/4645 tham số. Multi-step direct multi-output có weights riêng, không recursive. Model/adapter CPU float64 theo lựa chọn người dùng; không đổi shape/lịch sử/split của TV2. Adapter giữ ID/version/pairing, tách input khỏi targets.

Trace tái dựng gates bằng weights/bias thực, đối chiếu state/forward với rtol1e-10/atol1e-12 float64, no_grad/eval và không thay input/weights/gradients/mode. Đây là phép tính verified, không giải thích thị trường hoặc API đã phê duyệt. Persistence helper kiểm version/source hashes/scaler/horizon/lookback/checksum/actual dtype trước strict load, từ chối diagnostic untrained mặc định.

99/99 tests trên venv sạch, integration5460 samples và trace6 stages trong gói giải nén đã đạt local. Notebook03 ghi từng mục/cells/output; hướng dẫn consumer docs/TV3_Handoff_TV4_TV6.md, kết quả reports/audits/TV3_Final_Handoff.md. Chưa có training/checkpoint AAPL hoặc metric; TV4 làm training/selection, TV6 release/inference/eval. Không kết luận LSTM/CNN vượt persistence từ tests kỹ thuật.

## TV2 — preprocessing và bàn giao local (22/11/2026)

Pipeline hiện có: accept snapshot TV1/hash/provenance → gán split theo ngày target → fit scaler trên toàn train 2015–2022 → lưu/nạp scaler → tạo windows1/5 từ lịch sử liên tục → kiểm contract/input-only → audit leakage → đóng gói/tái lập. Code thuộc backend/data/preparation, backend/data/transforms, backend/artifacts (persistence) và backend/audit; không gọi model/training/API.

X float64 (B,30,1), y float64 (B,1)/(B,5), raw USD và ngày/ID/version giữ trong records input/target riêng. Lịch sử từ split trước được dùng khi đã quan sát; 5 target phải cùng split. Scaler chỉ fit train, mọi đường load/verify/inference adapter không refit. Tạo tensor model cần adapter riêng.

51/51 tests và kiểm tra ZIP giải nén độc lập bằng venv sạch đã đạt; X/y/indices nạp lại bằng dựng mới, hashes giữ nguyên. Chi tiết artifacts/lệnh/logs/giới hạn: docs/TV2_Setup_and_Handoff.md và reports/audits/TV2_Final_Handoff.md. Chưa có xác nhận máy khác hoặc thực nghiệm model; không suy ra LSTM/CNN hiệu quả từ tests preprocessing.

Trạng thái: đã có implementation phần dữ liệu TV1 trong workspace; model/training/API/web chưa được nghiệm thu trong phần việc này.

## Implementation TV1 hiện tại

- `backend/data/acquisition/downloader.py`: snapshot AAPL 2015–2025, metadata/hash, từ chối version trùng và exclusive creation.
- `backend/data/validation/provenance.py`: khai báo nguồn/version/AAPL/USD/phạm vi/chính sách/hash khớp raw.
- `backend/data/validation/validator.py`: ngày/giá/trùng/thứ tự/lịch phiên/OHLCV, cảnh báo giữ biến động lớn, xuất bảng chuẩn không ghi đè.
- `backend/data/validation/standard_output.py`: nghiệm thu schema/ngày/giá/hash sau audit chất lượng.
- `scripts/`: verify/package, runner tests, build/execute notebook và kiểm chứng workspace riêng; hướng dẫn tại `docs/TV1_Setup_and_Reproduce.md`.
- `tests/data/`: 34 test methods và nhiều subcase; fixture tổng hợp/mock mạng được tách khỏi kiểm tra artifacts thật.

Notebook trình bày flow hạng mục 1–10 và bảng tổng audit; không fit scaler/windowing hoặc training. Không coi metadata/hash là xác thực độc lập sàn, hoặc workspace riêng cùng máy là máy thành viên khác.

## Nội dung cần hoàn thiện

Điền bằng hoạt động thực tế trong đúng phạm vi Define/Design.

## Bằng chứng

Liên kết dataset version, run/release, logs, audit và phép kiểm tra liên quan khi có. Không điền số liệu giả hoặc kết luận trước thực nghiệm.

## TV5 — tiếp nhận CNN một bước

Đã nhận CNNOneStep và CNNOneStepConfig từ PR #9 vào backend/models/cnn_one_step, giữ nguyên source ở mục 1. Kiến trúc hiện có hai Conv1d 1→16→32, ReLU, MaxPool2, Flatten/Dropout0,1 và Linear 480→32→1. Tổng 17.057 tham số. Baseline 7/7 unit tests đạt trong workspace, forward tổng hợp (2,30,1) trả (2,1).

Dtype float32 hiện là mặc định của source tác giả, còn phải chốt cùng contract ở mục 2. CNN chưa có training AAPL hoặc kết quả đánh giá chính thức. Notebook TV5 ghi đầy đủ quá trình tiếp nhận. [Báo cáo mục 1](audits/TV5_Item1_Source_Intake.md)

### TV5 mục 2 — contract đã cập nhật

Model hiện dùng CPU float64 tường minh, giữ kiến trúc phương án A và 17.057 tham số. Input (B,30,1), output (B,1), kiểm cấu hình và số hữu hạn. Bảy tests tiếp nhận đã được cập nhật dtype và bổ sung tests contract, tổng 26 tests đạt. Các ghi nhận float32 trong mục tiếp nhận là lịch sử source ban đầu. [Báo cáo mục 2](audits/TV5_Item2_Architecture_Contract.md)
# TV5 hoàn thiện local ngày26/11/2026

CNN một bước CPU float64,17.057 tham số, dùng dữ liệu/scaler TV2 và loop TV4 chung. Config lock phương ánA,3 seed/146 epoch, research checkpoint/provenance/reload và monitoring có bằng chứng. So sánh250 validation2023 theo USD cho thấy persistence thấp hơn cả6 model, LSTM trung bình thấp hơn CNN. Không tuning sau so sánh hoặc đánh giá hiệu năng test. Xem [audit TV5 cuối](audits/TV5_Final_Handoff.md) và [setup/bàn giao](../docs/TV5_Setup_and_Handoff.md). Đây là bổ sung TV5, không thay nghiệm thu TV6/API/test cuối.

