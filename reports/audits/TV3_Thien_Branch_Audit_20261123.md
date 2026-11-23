# Audit nhánh Thien-code137-patch-1 — 23/11/2026

## Cập nhật workspace sau yêu cầu xử lý mục 1

Đã tiếp nhận10 file Python đúng module, giữ nguyên nội dung tác giả; workspace thực chạy55/55 tests đạt. Xem `reports/audits/TV3_Progress.md` và evidence `logs/audit/tv3_tests_20261123T020457014778Z/summary.json`. Nhánh remote và checkout audit gốc không đổi; các phát hiện bản nguyên trạng bên dưới vẫn còn hiệu lực với head GitHub đã audit. Các mục2–6 chưa hoàn thành chỉ vì tests nền đã đạt.

## Kết luận

Nhánh có source LSTM một/năm bước, model trace và 4 file pytest; đúng phạm vi TV3 theo phân công. Kiến trúc có thể tái sử dụng sau sửa bố trí file. **Chưa merge nguyên trạng** vì checkout hiện tại không chạy được tests theo lệnh README. Không sửa source nhánh, không merge/push/comment PR trong audit.

Đã kiểm tra danh sách nhánh và PR bằng GitHub connector: Tâm=b1bc2d15af789d558c9f75d2bb17c79b4db99655; TV2-Huyền=84ac389539c93a5033744ef3e9df9f9108a03b80; Thien-code137-patch-1=1f209b70c5690fb5e41b3b26d8eab36b2b6c029d; main=e45c064c2862d4793877a103ce13161c03843da9. Nhánh Thiện trùng head PR #6, open/chưa merge, chưa có commit mới hơn head đã thấy ở lần kiểm tra trước. PR #3/#4 hiện closed nhưng không merged; #1/#2/#5/#7/#8 vẫn open. Đây là bản chụp trạng thái lúc audit, không thay cho kiểm tra lại trước merge.

## Phát hiện cần xử lý

1. **P1 — đặt source sai thư mục, public import không hoạt động.** Các file nằm trong `lstm_one_step/`, `lstm_multi_step/`, `model_trace/` cấp gốc. Nhưng model multi-step, __init__, trace và cả tests đều import từ `backend.models...` / `backend.model_trace...`. Các thư mục backend đúng vị trí chỉ có README. Lệnh pytest từ gốc nhánh gặp **4 errors during collection**, chưa chạy test nào. Cần bố trí vào backend/models/lstm_one_step, backend/models/lstm_multi_step và backend/model_trace theo rule; cập nhật FILE_STRUCTURE, không tạo thêm module top-level ngoài cấu trúc. Đây là sửa bố trí file cần được thống nhất khi thực hiện, audit chưa tự làm trên nhánh.
2. **P2 — cần adapter dtype cho TV2 chính thức.** TV2 xuất X/y float64; model mặc định float32 và chủ động từ chối input khác dtype. `torch.from_numpy(batch['X'])` trực tiếp sẽ TypeError. Không phải lỗi toán học của LSTM; consumer cần cast có chủ đích như `torch.as_tensor(X,dtype=torch.float32,device='cpu')` và y cùng dtype cho loss; đối chiếu dung sai sau cast ở giai đoạn tích hợp. Không sửa dữ liệu/scaler TV2 để che lỗi adapter.
3. **P2 — test TV2 chưa kiểm chứng module hiện tại.** test_tv2_sample_format trong test_lstm_contract.py tạo dict input_scaled/target_scaled float32 theo PR #2 cũ. TV2 chính thức hiện có batch X/y và input/target records riêng. README nhắc snapshot aapl_2015_2025_v1 và tests/bản sao preprocessing tạm đã xóa; không thể tái lập tuyên bố tích hợp đó chỉ từ source hiện có. Cần tests tích hợp với loader/artifact chính thức và version/hash cụ thể. Probe lần này chỉ kiểm tra forward/trace, không nghiệm thu training.
4. **P2 — thiếu môi trường và bằng chứng chạy có thể nhận lại.** Nhánh không có requirements/lock cho torch/pytest, không có log 55 tests, checkpoint/training artifact chính thức hoặc bằng chứng chạy máy khác. Không dùng kết quả README để tuyên bố nhánh nguyên trạng chạy được. Checkpoint/training không phải yêu cầu hoàn tất riêng TV3 architecture, nhưng phải phân biệt rõ với nghiệm thu toàn project.

## Phần đúng và nên giữ

- LSTM 1 lớp, batch_first, mặc định một feature/hidden32; Linear cuối ra1 hoặc5, không activation giá cuối, không squeeze batch.
- h/c zero mới mỗi forward đúng dtype/device, không giữ state giữa mẫu. Multi-step tạo trọng số riêng, direct multi-output, không recursive và không dùng target trong forward.
- Kiểm tra tensor rank/feature/empty/dtype/device/finite và output finite; không phụ thuộc scaler/training/API.
- Tests có ý nghĩa: shape, parameter count, gradient/optimizer smoke, independence/batch ordering, state zero mới, state_dict roundtrip, invalid values, trace read-only/mismatch.
- Trace tái dựng gates theo i/f/g/o từ trọng số model, đối chiếu hidden/cell từng bước và output; no_grad/eval, không đổi trọng số. Đây là reconstructed-and-verified trace, không phải hook gates trực tiếp hoặc giải thích nguyên nhân thị trường. Schema trace là đề xuất nội bộ, chưa coi là API đã chốt.
- Cho phép T=10/30/60 đúng hướng thí nghiệm có kế hoạch; không phải lỗi vì mặc định project30.

## Kiểm chứng thực chạy

Checkout audit `.venv/tv3_review_20261123`, HEAD cố định như trên. Bản bố trí chẩn đoán `.venv/tv3_layout_probe_20261123`: chỉ copy nguyên nội dung source vào đúng backend paths, không sửa thuật toán/tests. Không thay checkout gốc hoặc workspace implementation TV3.

Môi trường `.venv/tv3_review_env` riêng, kế thừa site packages; Python3.13.7, torch2.14.1+cpu, pytest9.2.0, numpy2.4.4, sklearn1.9.1. Cài pytest/exchange_calendars ở venv audit, không sửa TV1/TV2. Đây là môi trường audit phát triển, chưa kiểm chứng sạch/lock/máy khác. Child tests dùng OMP/MKL threads=1.

| Phép kiểm tra | Kết quả |
|---|---|
| `python -m pytest tests/models -q -p no:cacheprovider` trên nguyên trạng | Exit2; 4 lỗi collection do import |
| Cùng lệnh trên bản chỉ bố trí lại file | **55 passed, 8.41s**, exit0 |
| Số tham số default | One-step4513; multi-step4645 |
| TV2 thật → model default, giữ float64 | TypeError (đúng guard dtype) |
| TV2 thật → cast float32 CPU → forward | 8 mẫu đầu mỗi split/mode, tổng48 lượt mẫu; output (8,1)/(8,5), hữu hạn |
| Inverse output bằng scaler TV2 | Shape hợp lệ, không là metric/độ chính xác dự báo |
| Trace trên một input train thật mỗi mode | Đạt rtol1e-5/atol1e-6; max hidden/cell abs error khoảng5.96e-8 |

Evidence original/layout: `logs/audit/tv3_branch_20261123T014802456231Z/summary.json`, original.log, layout_only.log. Evidence probe TV2 thật: `logs/audit/tv3_tv2_integration_20261123T014851263596Z/summary.json`.

Probe dùng snapshot TV2 đã chốt aapl_2015_2025_acq_20261119T141302002415Z, scaler aapl_scaler_20261120T124720810874Z, prepared tv2_prepared_20261122T145943242978Z, xác minh TV1/hash và load artifacts trước. Model trọng số khởi tạo ngẫu nhiên seed42 cho smoke test, không checkpoint đã train. Không tính MAE/RMSE, không tuning/chọn model bằng test, không phát biểu dự báo hiệu quả. Không xác nhận 2 ca tích hợp cũ đã xóa của tác giả.

## Thứ tự tích hợp đề xuất

1. Bố trí đúng module và giữ nguyên kiến trúc đang qua55 tests; cập nhật chỉ mục/import docs.
2. Khóa dependency CPU, lưu logs trên checkout chạy được; tái lập trên môi trường sạch.
3. Thay fixture TV2 cũ bằng tests consumer X/y chính thức, cast float32 và xác minh shape/ngày/ID/version/scaler.
4. Nghiệm thu architecture/trace TV3; phối hợp TV4 cho train/validation/checkpoint riêng1/5 bước. Chưa đưa schema trace thành API khi TV6 chưa thống nhất.

Nguồn: https://github.com/baochan24/Stock_Forecasting_Group4/tree/Thien-code137-patch-1 ; https://github.com/baochan24/Stock_Forecasting_Group4/pull/6 ; rule.md, docs/01_Project_Description_and_Foundation.md, docs/03_Module_Boundaries.md, docs/04_Data_Flow_and_Contracts.md, docs/12_Team_Assignment.md. docs/14_Module_Interfaces.md trên chính nhánh cũng xác định import backend đúng vị trí; không lấy tài liệu nhánh tự động thay quyết định workspace.
