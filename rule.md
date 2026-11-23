# Quy tắc làm việc — coursework Stock Forecasting Group 4

Cập nhật 20/11/2026 theo yêu cầu trực tiếp của người dùng. Áp dụng tại workspace này cho code, audit PR, notebook, báo cáo và quyết định triển khai. Đây là đồ án coursework lớn: tính đúng phương pháp, bằng chứng và khả năng giải thích quan trọng hơn số lượng tính năng hoặc tốc độ đánh dấu hoàn thành.

## 1. Đọc cốt lõi trước khi code hoặc quyết định

Hai tài liệu đề gốc đã có nội dung và được đọc ngày 21/11/2026:

- `docs/đề_yêu_cầu.md`: Topic 4 — Regression, Yahoo Finance, dự báo giá phiên tiếp theo từ chuỗi quá khứ bằng LSTM; mở rộng multi-step và CNN vs. LSTM.
- `docs/yêu_cầu_mẫu_đề_tài.md`: 10 mục đăng ký đề tài và 7 nhóm sản phẩm báo cáo cần bao phủ.

Đọc hai file này trước danh sách thiết kế dưới đây khi bắt đầu hạng mục mới; nếu đã đọc và không đổi, dùng lại ngữ cảnh. Phân biệt yêu cầu đề gốc với quyết định nhóm: AAPL/2015–2025/lookback 30/split/CPU/StandardScaler/5 bước/persistence là thiết kế cụ thể của project, không gán thành câu chữ bắt buộc của đề gốc. Hai phần mở rộng đã được nhóm đưa vào phạm vi project, không tự bỏ.

Khi nghiệm thu sản phẩm, đối chiếu đủ 10 mục đăng ký: tên, hướng chính, người dùng/vấn đề, mục tiêu đo lường, dữ liệu (kể cả quyền sử dụng/phương án thay thế), phạm vi, phương pháp/baseline, sản phẩm, đánh giá, kế hoạch/rủi ro. Phần chưa có bằng chứng phải ghi còn mở; không bịa quyền sử dụng, deadline hoặc kết quả để điền đủ mẫu. Flow TV2 vẫn giữ nguyên vì đề gốc không thay contract preprocessing đã chốt.

Trước tác vụ triển khai mới, đọc các tài liệu sau theo thứ tự; nếu đã đọc trong phiên và tài liệu không đổi, dùng lại ngữ cảnh, không cần đọc lặp máy móc:

1. `docs/01_Project_Description_and_Foundation.md`: bài toán, câu hỏi nghiên cứu, phạm vi, quy tắc thực nghiệm và yêu cầu coursework.
2. `docs/03_Module_Boundaries.md` và `docs/04_Data_Flow_and_Contracts.md`: trách nhiệm module, chiều phụ thuộc, input/output/ngày/shape.
3. `docs/12_Team_Assignment.md`: phần việc TV1–TV6 và đầu ra bàn giao.
4. `docs/11_Decision_Log.md` và `docs/10_Open_Decisions.md`: điều đã chốt, điều còn mở; không tự biến đề xuất thành quyết định.
5. README của module sắp sửa, code/test liên quan và audit mới nhất của hạng mục đang làm.

Đọc thêm `docs/02_System_Architecture.md` khi đổi cách ghép module; `docs/05_API_Contract.md` khi làm API; tài liệu setup/reproducibility khi đổi môi trường hoặc bàn giao. Đối chiếu đề gốc Topic 4 và yêu cầu coursework nếu chúng có trong workspace. Nếu thiếu, nêu rõ chưa đối chiếu trực tiếp đề gốc, không bịa nội dung; dùng tài liệu project đã chốt cho công việc không phụ thuộc phần thiếu.

Trước khi sửa, xác định được: **đang làm mục nào → phục vụ yêu cầu nào của bài → nhận gì → trả gì → kiểm chứng bằng gì**. Giải thích ngắn cho người dùng khi bắt đầu hạng mục. Không code theo riêng tiêu đề PR hoặc đoạn hội thoại gần nhất mà bỏ contract gốc.

Tài liệu mô tả thiết kế có thể ghi trạng thái ở thời điểm dựng nền. Trạng thái triển khai hiện tại phải đối chiếu source, kết quả chạy và audit mới nhất; không coi trạng thái lịch sử là bằng chứng hiện tại. Khi tài liệu và code mâu thuẫn, ghi rõ mâu thuẫn và giải quyết trong phạm vi đã được yêu cầu; không tự sửa thiết kế để hợp thức hóa code sai.

## 2. Mục tiêu và phạm vi cố định

- Bài toán chính: dùng 30 phiên adjusted close AAPL để dự báo adjusted close phiên tiếp theo; đánh giá LSTM so với persistence.
- Yahoo Finance/yfinance, dữ liệu ngày 2015–2025, đơn vị USD, một đặc trưng giá; ghi chính sách điều chỉnh hồi cứu và giới hạn point-in-time.
- Phạm vi mô hình: LSTM một bước, CNN 1D một bước, LSTM direct multi-output năm bước và persistence tương ứng. CPU, Python/PyTorch theo thiết kế.
- Không yêu cầu LSTM thắng baseline; không dùng biểu đồ bám giá làm bằng chứng hiệu quả. Không suy rộng thành lợi nhuận giao dịch.
- Không tự thêm mô hình, ticker, giao dịch, đăng nhập, real-time hoặc tính năng ngoài Define/Design. Cấu hình khởi đầu chưa phải cấu hình tối ưu đã chứng minh.
- Báo cáo phải bao phủ: vấn đề/phạm vi, dữ liệu, mã nguồn, cài đặt/chạy, demo, so sánh baseline, phân tích lỗi/giới hạn.

## 3. Bám flow, làm từng hạng mục

Flow toàn project: **TV1 dữ liệu → TV2 preprocessing → TV3/TV4 LSTM và training → TV5 CNN cùng pipeline → TV6 đánh giá/tích hợp/phát hành**. Các thành viên có thể làm độc lập theo contract; không coi phần sau hoàn thành khi đầu vào chưa được xác minh.

Flow TV2 đang áp dụng:

| Mục | Phạm vi |
|---|---|
| 1 | Module nền, interface, kiểm tra đầu vào |
| 2 | Tiếp nhận snapshot TV1, xác minh hash/metadata và giữ dataset_version |
| 3 | Chia tập theo ngày target, bảo toàn lịch sử cho windowing |
| 4 | Fit scaler train, lưu/nạp và metadata tương ứng |
| 5 | Scale/inverse dùng scaler đã lưu, shape và dung sai |
| 6 | Windowing một bước, lookback 30 |
| 7 | Windowing năm bước, toàn bộ target cùng split |
| 8 | Forecast Input/Target riêng, ID/ngày/version/shape |
| 9 | Audit leakage, đối chiếu cửa sổ bằng tay, kiểm tra ranh giới |
| 10 | Môi trường, lệnh tái lập, manifest và bàn giao consumer |

Trạng thái cập nhật ở `reports/audits/TV2_PR_Audit_20261120.md`, không dùng rule.md làm log hoàn thành. Tại thời điểm lập rule: mục 1–2 đã có bằng chứng local, bước kế tiếp là mục 3. Mọi phiên sau phải kiểm tra trạng thái thực tế mới nhất.

Khi người dùng yêu cầu một mục, hoàn thành mục đó và các phụ thuộc cần thiết; không tự triển khai các mục sau hoặc chuyển sang API/model/UI. Chỉ báo trước bước tiếp theo. Audit PR chỉ đọc/kiểm tra và báo cáo, không mặc nhiên merge/push. PR mới có thể tham khảo, nhưng phải so với code local và contract trước khi tiếp nhận; không ghi đè phần đã sửa bằng code kém phù hợp hơn.

## 4. Bất biến dữ liệu và thực nghiệm

- Split theo **ngày target**: train 2015–2022, validation 2023, test 2024–2025. Không random split theo thời gian.
- Input được dùng lịch sử đã quan sát từ tập trước. Không cắt riêng lịch sử của từng tập rồi làm mất 30 target đầu validation/test. Không dùng tương lai để điền quá khứ.
- Multi-step: cả 5 target cùng split, tính theo phiên dataset, không cộng ngày lịch. Không đưa target tương lai vào inference.
- StandardScaler chỉ fit giá train; dùng lại cho validation/test/inference. Liên kết scaler với dataset/version/hash và phạm vi fit. Không nhân bản logic fit trong transforms.
- Input LSTM `(B,30,1)`; target `(B,1)` hoặc `(B,5)`. CNN giữ cùng mẫu/ngày dù đổi thứ tự chiều. Dtype phải được mô tả ở adapter, không âm thầm thay shape/ý nghĩa feature.
- Forecast Input và Target tuân thủ `docs/04_Data_Flow_and_Contracts.md`; inference chỉ nhận input. ID phải đủ phân biệt phiên bản/chế độ.
- MAE/RMSE trên giá gốc USD, không làm tròn trước metric; multi-step báo từng horizon 1–5; so sánh trên cùng tập mẫu.
- Chọn model/checkpoint bằng validation, khóa trước đánh giá test; không dùng test để tuning/chọn seed. Kiểm tra schema/hash/độ phủ của phân đoạn test không phải đánh giá hiệu năng model, phải phân biệt hai việc này.
- Ba seed định trước cho cấu hình cuối; báo kết quả thật, không chọn seed thắng test. Không train hoặc tính metric nếu hạng mục hiện tại chỉ là nhận/chia dữ liệu.

## 5. Tổ chức code, artifacts và môi trường

- Giữ thư mục cấp cao hiện có: backend, frontend, docs, reports, data, experiments, artifacts, logs, tests, scripts, notebooks. Không tự di chuyển/đổi tên/xóa file hoặc cấu trúc đã có; thay đổi cấu trúc cần thống nhất theo quy tắc nhóm.
- Code trong module tương ứng; tests trong `tests/<module>`; CLI/build/execute notebook trong `scripts/`; notebook trong `notebooks/`; audit trong `reports/audits/`. Giữ README trách nhiệm module, cập nhật chỉ mục `FILE_STRUCTURE.md` khi thêm file.
- TV1 sở hữu acquisition/validation, TV2 preparation/transforms; TV3 models/trace LSTM, TV4 training, TV5 CNN, TV6 baseline/evaluation/inference/integration/API/frontend. Dùng lại validation/provenance TV1, không tạo pipeline cleaning song song trong TV2.
- Snapshot gốc và run cũ bất biến. Không tự loại/sửa/điền phiên; cần xử lý phải có quyết định và phiên bản mới. Không hard-code số dòng/mẫu của một snapshot thành quy tắc cho mọi dataset.
- Chỉ source/docs/config và báo cáo có chủ đích vào Git; không dataset/scaler/checkpoint/log sinh ra/ZIP/venv/secrets. Giữ thay đổi local/staged của người dùng, không reset/clean hoặc merge ngoài phạm vi.
- Dùng môi trường phù hợp và ghi đúng Python/dependencies. Không chèn `.venv/eda_deps` vào sys.path; không sửa môi trường TV1 đã kiểm chứng để tiện chạy TV2. Thiếu dependency phải ghi nhận, không giả định chạy được.
- Cập nhật file thực tế tại workspace/VS Code trước khi chia sẻ bản sao. Không tự upload Drive, commit/push hoặc merge nếu tác vụ hiện tại chưa cho phép; tôn trọng các ủy quyền cụ thể đang có trong phiên.

## 6. Nghiệm thu và cập nhật sau mỗi mục

Yêu cầu bổ sung của người dùng23/11/2026: mỗi phần TV có notebook riêng trong notebooks/; mỗi hạng mục gồm cell giải thích mục tiêu/input/output, cell gọi backend và cell kiểm chứng/bằng chứng, lưu output thật để có thể trình bày giảng viên. Hiện TV1 dùng01_AAPL_Data_Exploration, TV2 dùng02_TV2_Preprocessing_and_Audit, TV3 dùng03_TV3_LSTM_Development_and_Tests. Sau mỗi mục tiếp theo phải đồng bộ notebook TV tương ứng cùng builder trong scripts và chạy lại các cells bị ảnh hưởng. Không sửa notebook TV1 để ghi phần TV khác; không nhân bản pipeline hoặc ghi pass trước khi chạy. TV4–TV6 tạo notebook khi bắt đầu phần đó, các phần chưa làm phải ghi chờ. Xem notebooks/README.md cho cách build/execute, giữ nguyên output không liên quan khi chỉ cập nhật một TV.

1. Kiểm tra code đúng contract và ranh giới module; chạy kiểm chứng phù hợp với thay đổi, ưu tiên test có khả năng phát hiện lỗi thực tế.
2. Khi làm với dữ liệu thật, kiểm tra snapshot/hash đúng phiên bản và lưu bằng chứng; fixture tổng hợp/mock phải gắn nhãn rõ, không dùng thay chứng nhận end-to-end.
3. Ghi lệnh, môi trường, kết quả, phạm vi được kiểm tra và giới hạn. Phân biệt chưa làm, có code, đã test local và đã xác nhận máy khác. Lỗi môi trường phải ghi riêng, không tính thành test đạt.
4. Cập nhật audit/checklist và README liên quan sau thay đổi. Nếu hạng mục có notebook được người dùng chỉ định, cập nhật notebook local đó và output cần thiết; không ghi TV2 vào notebook EDA TV1 nếu chưa được yêu cầu. Không dùng Drive thay cho cập nhật local.
5. Chỉ chốt hoàn thành khi có đầu ra và kiểm chứng đúng phạm vi. Một vài test helper đạt không chứng minh cả pipeline không leakage. Không tạo kết quả giả hoặc ghi hoàn thành trước khi chạy.
6. Báo ngắn: đã làm gì, kiểm chứng gì, còn giới hạn nào, bước tiếp theo theo flow. Không tự đổi số thứ tự hoặc mở thêm checklist thay thế khiến người dùng mất dấu.

## 7. Quyết định và thay đổi quy tắc

Quyết định thay phạm vi, split, feature, shape/interface, mô hình, cách đánh giá hoặc trách nhiệm phải có sự thống nhất và ghi `docs/11_Decision_Log.md` kèm lý do/ảnh hưởng/người quyết định. Không coi PR hoặc gợi ý AI là phê duyệt thiết kế. Các sửa lỗi thường quy trong phạm vi người dùng đã giao được thực hiện trực tiếp, không hỏi lại chỉ vì có rule.

Quy tắc này cụ thể hóa cách làm tại workspace theo yêu cầu người dùng; không phải tuyên bố cả nhóm đã bỏ phiếu đổi thiết kế. Bản `Stock_Forecasting_Group4/rule.md` thuộc checkout lồng bên trong được giữ nguyên. Với thiết kế project, đối chiếu tài liệu gốc và quyết định đã chốt; nếu có mâu thuẫn chưa giải quyết ảnh hưởng trực tiếp tác vụ, nêu rõ và xin làm rõ, đồng thời tiếp tục phần độc lập có thể làm.
