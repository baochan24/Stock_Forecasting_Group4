# TV6 — kết quả thử nghiệm cải tiến residual

Hoàn thành local27/11/2026 theo yêu cầu thử sửa và kiểm tra cải thiện. **Có cải thiện rõ so với đối chứng dự báo mức giá; chưa chứng minh vượt persistence một cách bền vững hoặc trên test độc lập mới.**

## Đã thay đổi gì

Phiên bản riêng `origin-centered-price-delta-v1`:

- Input=(history−giá cuối cửa sổ)/scale_train; target=(future−giá cuối cửa sổ)/scale_train.
- Output USD=giá cuối cửa sổ+scale_train×delta dự báo. H5 là5delta cùng origin, không recursive.
- Head output khởi tạo0 để bắt đầu tại persistence. Core LSTM/CNN, số tham số và CPUfloat64 giữ nguyên.
- Đây là gói cải tiến3yếu tố, không phải ablation tách tác động riêng. Với weights/scale cố định, dịch mọi giá input thêm cùng một hằng số giữ nguyên relative input và dịch output cùng hằng số; kiểm tra fixture đã đạt. Điều này loại bỏ một dạng nhạy theo mức giá tuyệt đối, không bảo đảm hiệu quả khi thị trường thay đổi phức tạp.

Không sửa dữ liệu hoặc scaler/model/protocol v1; không chọn lại seed theo test.36checkpoint nghiên cứu mới, không tự động đưa vào release/catalog. Contract và kế hoạch: [TV6_Residual_Development_v1.md](../../docs/TV6_Residual_Development_v1.md).

## Kế hoạch và số liệu thật

36runs=2fold validation2022/2023×3tasks×2biểu diễn×3seeds42/123/456. Fold2022 train đến2021; fold2023 train đến2022. Scaler fit riêng trên giá train từngfold. Adam/MSE,lr0.001,batch32,max100epoch,patience10; tổng1055epoch,733,19giây chạy ghi nhận, không tính các bước audit/notebook. Mỗi run dùng bestvalidation checkpoint, không bỏseed.

MAE USD, neural lấy mean3seed; H5 là overall trên mọi mẫu×5horizon:

| Validation | Task | Absolute control train lại | Residual mới | Persistence | Giảm MAE so control |
|---|---|---:|---:|---:|---:|
| 2022 | LSTM h1 | 4,071180 | 2,596975 | 2,602120 | 36,21% |
| 2022 | CNN h1 | 3,895882 | 2,593409 | 2,602120 | 33,43% |
| 2022 | LSTM h5 | 5,486088 | 4,323299 | **4,313107** | 21,20% |
| 2023 | LSTM h1 | 2,801693 | 1,619409 | 1,636779 | 42,20% |
| 2023 | CNN h1 | 2,160442 | 1,620033 | 1,636779 | 25,01% |
| 2023 | LSTM h5 | 4,153028 | 2,931102 | 2,984996 | 29,42% |

RMSE trên validation2023: LSTMh1 control3,414598→residual2,106283 (baseline2,120593); CNNh1 2,773064→2,106200 (baseline2,120593); LSTMh5overall5,044827→3,841833 (baseline3,903600). Đủ MAE/RMSE/bias/từngseed/từnghorizon/std mẫu ddof1 có trong notebook vàCSV, không ensemble.

Các control trong bảng được huấn luyện lại cùng mẫu/budget/sampler với residual, **không phải điểm v1 đã công bố**. H1 dùng toàn bộ cửa sổlb30 thay vì common60; CLI này shuffle minibatch trong train, còn runner v1shuffleFalse. Chia tập vẫn theo thời gian, validation không shuffle. Phép so sánh ghép cặp hiện tại không bị khác sampler giữacontrol/residual, nhưng không dùng nó để quy toàn bộ chênh lệch vớiv1 cho riêng delta target.

## Diễn giải

Residual giảm MAE21–42% so control trên cả6task/fold, và độ phân tán giữa3seed thấp hơn trong lần chạy này. Trên validation2023, bias trung bình LSTMh1 từ−0,952 xuống−0,026USD; CNNh1 từ+0,241 xuống−0,043USD; LSTMh5 từ−2,155 xuống−0,476USD. Đây là bằng chứng cải thiện trên development, không phải xác nhận đã chữa nguyên nhân test bằng thí nghiệm nhân quả.

So với persistence, MAEh1 mới chỉ thấp hơn khoảng0,20–0,33% ở2022 và1,02–1,06% ở2023. H5overall2023 thấp hơn1,81%, nhưng2022 cao hơn0,24%. Không có threshold thực tiễn/phép kiểm significance đã khóa; không tuyên bố vượt baseline đáng kể hoặc ổn định. Overlapping h5 windows không độc lập. Các mạng đang dự báo gần persistence; lợi thế lớn so control chủ yếu phản ánh tránh lỗi của control, không đồng nghĩa học được quy luật cổ phiếu mạnh.

## Kiểm chứng

- 10tests mới đạt: tính tay/dịch mức giá/encode-decode/h1-h5/zero-delta=persistence/invalidscale/shapes/không sửainput/ranh giới mọi target cùngfold/pair IDs. JUnit `logs/audit/tv6_residual_readiness_tests.xml`.
- Training loop, seed manager, coremodels, save/loadscaler và metric dùng lại module đã nghiệm thu.36run thật, checkpoint best đượcrestore và reload file, dự đoán kiểm tra khớp tuyệt đối.
- Audit độc lập `scripts/audit_tv6_residual_development.py` đạt: đủ36uniqueruns/6pairedcohorts; full-year keys derive từ lịch snapshot; actual vàbaseline khớp raw; metric bằng math.fsum/sqrt, aggregate bằng statistics; scalermean/variance chỉtrain; MSE USD khớp bestvalMSE×scale²; bestepoch khớp history; hashcheckpoint vàsource khớp.
- Dữ liệu/artifacts/source đã pin và protocol v1 giữ nguyên hash. Không đọc test targetJSON/NPZ hoặc làm testforward mới trong thử nghiệm.
- Notebook06 đã lưu22cells/11code cells có output, bảng từngseed/horizon/mean/std, so sánh2fold và6panel loss trênfold2023. Builder đồng bộ; Run All chỉ đọc kết quả, không train lại.

Receipt `logs/audit/tv6_residual_development_20261127T012509759710Z/summary.json`; audit `independent_audit.json`; notebook `notebook_verification.json`; checkpoints `artifacts/checkpoints/tv6_residual_development_20261127T012509759710Z/`. ScalerIDs vàhash riêng mỗifold trongmanifest. Chưa nghiệm thu máy thành viên khác.

## Giới hạn và trạng thái tiếp theo

Thử nghiệm được thiết kế sau khi đã thấy test2024–2025, nên2022/2023 là development và không thay thế bằng chứng held-out. Không ghi đè kết quả test cũ bằng bảng này, không sửa nhãn test thànhvalidation để hợp thức hóa tuning. Chưa đánh giá phiên bản mới trên dữ liệu tương lai chưa thấy; chưa promote model vào FrozenForecaster/API/demo. Bộ v1 vẫn dùng protocol/checkpoint cũ, không tự chuyển sang residual.

Hướng sửa đã có bằng chứng cải thiện development; giữ candidate và kết quả để tổng hợp phân tích lỗiTV6. Mục6 tổng thể chưa nghiệm thu hoàn chỉnh; các bước release/API/frontend còn theo flow riêng. Bước kiểm chứng tiếp theo cần protocol rõ ràng, phân biệt đánh giá sau phát triển trên test đã thấy với kiểm chứng tương lai độc lập; không tự chạy thêm vòng tuning.
