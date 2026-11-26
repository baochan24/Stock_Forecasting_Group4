# TV4 mục 7 — audit và thiết kế thực nghiệm

## Đối chiếu thông số cuối trước training

Đã đọc lại bốn YAML chính thức từ summary mục 7, xác minh SHA256 của scaler/prepared manifest và toàn bộ payload prepared. Đối chiếu target dates train 2015–2022, validation 2023, dtype float64, shape và số tham số model. Cả bốn cấu hình đạt. Một bước lookback 10/30/60 có cùng 1.954 mẫu train, 250 mẫu validation và 4.513 tham số. Năm bước lookback 30 có 1.980 mẫu train, 246 mẫu validation, 4.645 tham số.

Cấu hình chung là hidden 32, một lớp, một feature, Adam 0,001, batch 32, MSE, max_epochs 100, patience 10, clipping tắt, một luồng CPU và seeds 42/123/456. Output năm bước được factory suy ra từ forecast_length=5 dù YAML không ghi output_size. Bản YAML baseline một bước ở experiments/configs dùng đầy đủ 1.984 mẫu train; chạy thực nghiệm lookback phải dùng bốn YAML được liệt kê trong summary mục 7 để giữ đúng common target dates.

Điều kiện chạy đã sẵn sàng cho kế hoạch 12 run. Đợt đối chiếu này kiểm cấu hình và artifacts, không chạy huấn luyện. [Biên bản thông số cuối](../../logs/audit/tv4_pretrain_20261125T122223473143Z/summary.json)

## Hoàn thiện theo yêu cầu trước training

Kế hoạch mục 7 đã chốt cho 12 run, tối đa 1.200 epoch. Ba lookback một bước dùng cùng 1.954 mẫu train và 250 mẫu validation. Bốn cấu hình đã qua probe một epoch và kiểm CSV diagnostics. Hồi quy TV2/TV4/checkpoint đạt 128 tests, 96 subtests. Strict TV4 đạt 67/67 trong môi trường sạch. [Bằng chứng kế hoạch](../../logs/audit/tv4_item7_20261125T120957429763Z/summary.json) · [JUnit hồi quy](../../logs/audit/tv4_item7_20261125T120957429763Z/regression.xml) · [Strict TV4](../../logs/audit/tv4_tests_20261125T121649383002Z/summary.json)

Đã nạp mới cả bốn checkpoint của probe, đo lại validation MSE và đối chiếu với best loss đã lưu trong metadata, dung sai tương đối 1e-12. Summary ghi all_four_reload_mse_verified=true.

Khi TV5 so CNN với LSTM lookback 30, dùng cùng 1.954 mẫu train và 250 mẫu validation của nhóm common60 cùng các khóa mẫu đánh giá. Nếu dùng toàn bộ 1.984 mẫu train cho CNN phải tạo lại run đối ứng LSTM và ghi ngân sách bổ sung trước khi chạy. CNN cụ thể và ngân sách riêng vẫn thuộc nhiệm vụ TV5.

Runner strict giữ receipt intake gốc và đối chiếu riêng hash của các file TV2 được thay đổi theo yêu cầu mục 7 tại TV4_Item7_Source_Changes.json. Artifacts nguồn vẫn đối chiếu hash ban đầu. Những dòng ghi chờ hoặc chưa hỗ trợ bên dưới là audit trước khi thực hiện các sửa đổi này.

Theo yêu cầu người dùng hoàn thiện toàn bộ các việc audit, đã mở rộng pipeline 10/30/60. Cấu hình cũ mặc định 30 và artifacts gốc giữ nguyên. Artifacts mới kiểm coverage đầy đủ từng lookback trước khi chọn chung target có đủ 60 phiên lịch sử. Kế hoạch chính thức gồm 9 run một bước trên ba lookback và ba seed, cộng 3 run năm bước tại lookback 30. Tổng giới hạn 1.200 epoch. Chọn lookback bằng validation MSE trung bình ba seed, hòa đúng số lưu ưu tiên lookback ngắn hơn, báo std mẫu ddof=1.

Đã bổ sung hash toàn bộ backend và YAML vào metadata run và checkpoint, ghi cấu hình run, số luồng tính toán đặt mặc định 1 ở runner và tường minh trong YAML. CSV lưu train_seconds, validation_seconds và val_mse_per_horizon sau mỗi epoch. Khi checkpoint sau gặp lỗi, metrics vẫn giữ tham chiếu checkpoint trước đã ghi thành công. Giữ nguyên trạng thái failed/interrupted để tổng hợp run chính thức.

Runner tìm project root từ vị trí source, hỗ trợ YAML nằm trong thư mục audit. Lần probe đầu phát hiện đường dẫn sai và được ghi failed. Đã sửa đường dẫn trước chạy probe lại. Các kết quả failed giữ lại để truy vết.

Các phần audit ban đầu dưới đây mô tả trạng thái trước sửa và lý do thay đổi. Phiên bản hoàn thiện có bằng chứng ở logs/audit/tv4_item7_20261125T120957429763Z, gồm bốn cấu hình chính thức, artifacts tham chiếu, regression.xml và các probe một epoch.

## Tái kiểm tra trước training ngày 25/11/2026

Lượt mới chạy strict tests đạt 66/66, không skip, môi trường sạch và import đúng workspace. Kiểm tra lại AAPL cho cả hai horizon đạt, gồm provenance/hash, ngày, số mẫu và forward CPU float64. [Tests](../../logs/audit/tv4_tests_20261125T120434712517Z/summary.json) · [Dữ liệu thật](../../logs/audit/tv4_item3_20261125T120532955439Z/summary.json)

Kết luận sẵn sàng kỹ thuật cho pipeline lookback 30 đã smoke ở mục 6. Thiết kế toàn bộ thực nghiệm vẫn chờ khóa. Những việc cần hoàn tất trước run chính thức gồm phạm vi lookback 10/60, hash đầy đủ source model/transforms và YAML, lưu validation từng horizon cho run năm bước, và đặt rõ số luồng CPU ở entry point chạy chính thức. Runner chỉ ghi số luồng hiện có, script smoke mới trực tiếp đặt một luồng.

CSV hiện bỏ hai trường train_seconds/validation_seconds có trong kết quả trainer. Nếu cần tái lập bảng đo riêng cho run chính thức, cần lưu thêm các trường này hoặc summary riêng như smoke đã làm. Khi ghi checkpoint lỗi, CSV có epoch đã quan sát nhưng metadata lỗi chưa giữ đường dẫn checkpoint trước đó. Trạng thái failed giúp tránh coi run ấy là hoàn tất, cần bổ sung tham chiếu best đã lưu khi hoàn thiện nghiệm thu run lỗi.

Giới hạn kiểm chứng của bộ 66 tests gồm các phép thử tổng hợp. Hai horizon reload trên AAPL dựa bằng chứng mục 6, lượt tái kiểm này chạy lại data acceptance và tests, không chạy huấn luyện chính thức.

Ngày 25/11/2026. Phương án ban đầu và lịch sử audit được giữ bên dưới để đối chiếu với phần cập nhật hoàn thiện phía trên.

## Cơ sở kiểm tra

Đối chiếu rule.md, đề Topic 4, tài liệu nền mục 8–12, ranh giới và contract, phân công TV4, Decision Log và Open Decisions. Kiểm tra source factory, windowing, prepared artifacts, trainer, runner và bằng chứng mục 6. Đề gốc yêu cầu next-day LSTM cùng mở rộng multi-step và CNN. AAPL, lookback, seed và ngân sách là thiết kế nhóm.

## Kết quả audit

| Nội dung | Bằng chứng và kết luận |
|---|---|
| Nối dữ liệu và dtype | Hai horizon dùng snapshot/scaler/prepared có provenance, CPU float64 |
| Checkpoint | Smoke ba epoch nạp model mới, dự báo toàn validation bằng best trong RAM |
| Seed | Hai YAML có 42, 123, 456. Quy trình chính thức cần giữ cả ba và báo đầy đủ |
| Lookback | factory yêu cầu 30, windows.py cắt 30 phiên, prepared.py ghi và kiểm 30. Model hỗ trợ shape 10/60 chưa chứng minh pipeline hỗ trợ |
| Thời gian | Run mục 6 đo một luồng tính toán, interop 2. One-step train+validation ba epoch 6,210 giây, five-step 6,556 giây |
| Lịch sử | CSV lưu train/val/LR/thời gian tổng epoch. Trường thời gian train/validation mới trong kết quả RAM, summary smoke lưu tổng riêng |
| Hash nguồn | Metadata run ghi runner/manager/trainer/factory và provenance. Chưa có hash đầy đủ model/scaler transform hoặc config YAML như một manifest nghiệm thu cuối |
| Lỗi/ngắt | Exception và KeyboardInterrupt được ghi trạng thái. Kill cưỡng bức có thể để trạng thái running, cần kiểm run chưa hoàn tất khi tổng hợp |
| CNN | Kiến trúc/ngân sách CNN còn mở, cần quy tắc so sánh TV5 trước kết luận |
| Tập test | Đánh giá sau khi khóa cấu hình và quy tắc, TV6 chịu trách nhiệm |

## Đề xuất cấu hình cố định cho lookback 30

Hai LSTM một lớp hidden 32, một đặc trưng adjusted close. Output 1 và 5. CPU float64, một luồng tính toán và ghi số interop thực tế. Batch 32 giữ batch cuối, thứ tự thời gian, Adam learning rate 0,001, MSE, tối đa 100 epoch, patience 10. Giữ gradient clipping tắt theo cấu hình hiện có. Dừng và ghi lỗi nếu loss/gradient/trọng số không hữu hạn.

Train target 2015–2022, validation target 2023. Giữ scaler train của TV2 và các ID/hash đã ghim trong hai YAML. Checkpoint chọn bằng validation MSE nhỏ hơn nghiêm ngặt, hòa giữ epoch sớm hơn. MSE năm bước trung bình đều trên năm horizon. Đo lại loss từ model nạp từ đĩa.

Ngân sách chính gồm 2 horizon × 3 seed = 6 run, tối đa 600 epoch. Không mở lưới hidden size/LR trong kế hoạch này. Báo từng seed, trung bình và độ lệch chuẩn mẫu ddof=1. Trung bình các seed mô tả nhiều lần huấn luyện độc lập.

Nội suy đơn giản từ smoke 30 phiên cho 600 epoch là khoảng 1.277 giây, tương đương 21,3 phút train+validation. Đây là ước lượng để lập kế hoạch. Thời gian xác minh artifacts, ghi checkpoint, reload, tải nền và biến động hiệu năng làm tổng thực tế khác đi. Early stopping có thể giảm số epoch.

## Kế hoạch lookback cần thống nhất

Đề xuất giữ so sánh độ nhạy 10/30/60 cho LSTM một bước, mỗi lookback ba seed, cùng cấu hình và tối đa 100 epoch. Tổng 9 run một bước cộng 3 run năm bước tại lookback 30 là 12 run, tối đa 1.200 epoch. Các run lookback 30 dùng chung nếu đúng cùng tập mẫu và cấu hình, tránh đếm hai lần.

Để thực hiện cần bổ sung contract TV2 cho windowing/prepared 10/60, tạo artifacts mới với ID riêng, dùng giao target dates hợp lệ ở từng split và cùng scaler train. Đếm lại mẫu, audit pairing và leakage trước training. Cấu hình lookback 30 đã chạy với toàn bộ mẫu có thể cần run riêng nếu giao ngày làm thay đổi tập train. Ngân sách khi đó phải cập nhật trước run.

Chọn lookback bằng validation MSE trung bình ba seed trên cùng mẫu. Nếu hòa đúng số lưu, ưu tiên lookback ngắn hơn. Giữ báo cáo baseline lookback 30 cho CNN theo tài liệu nền. Kết quả 10/60 còn phụ thuộc triển khai và đo thời gian riêng, chưa thể ngoại suy chắc chắn từ smoke lookback 30.

## Điều kiện trước các run chính thức

Thống nhất phần lookback trước khi ghi Decision Log thành kế hoạch đã chốt. Lưu cấu hình và hash nguồn đầy đủ theo từng run. Mỗi run có model khởi tạo mới, manifest checkpoint, lịch sử, điều kiện CPU và xác minh reload. Multi-step cần bảng validation từng horizon ở run chính thức. Phân biệt run lỗi với run hoàn tất khi tổng hợp.

Sau khi khóa cấu hình, TV6 đánh giá MAE/RMSE USD, baseline persistence và CNN trên cùng khóa mẫu. Mọi kết quả test từng được xem trước khi sửa phải được ghi vào giới hạn nghiên cứu. Báo cáo hiện chỉ xác nhận các bằng chứng train/validation đã đọc.

## Kết luận nghiệm thu

Mục 7 đã có audit và phương án ngân sách cụ thể. Việc khóa toàn bộ thiết kế còn phụ thuộc quyết định triển khai lookback 10/60. Chưa đánh dấu hoàn thành toàn bộ mục 7.

Nguồn đo CPU tại [summary mục 6](../../logs/audit/tv4_item6_20261125T115308089469Z/summary.json). Source kiểm tra tại backend/experiments/runner/aapl_factories.py, backend/data/preparation/windows.py và backend/artifacts/prepared.py.
