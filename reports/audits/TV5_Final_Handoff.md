# TV5 — audit cuối và bàn giao

Ngày26/11/2026. Phạm vi coursework CNN một bước, cùng pipeline TV1/TV2/TV4 và so sánh validation với LSTM/persistence. Đối chiếu đề Topic4, rule.md, module boundaries/data contracts/team assignment/decision log và bằng chứng local, không suy từ checkout lồng.

## Audit mười hạng mục

| Mục | Sản phẩm và điều kiện đã kiểm |
|---|---|
| 1 | Intake PR9 commit/hash, source đặt đúng module, baseline7 tests lịch sử |
| 2 | CNN17.057 params, input(B,30,1)/output(B,1), CPU64, guards config/input/output |
| 3 | Same250 val/1.954 train, ID/ngày/arrays/provenance/scaler và forward dữ liệu thật |
| 4 | Gradient/Adam/dropout/train-eval/state_dict file thật, diagnostic tổng hợp |
| 5 | Factory/YAML CNN vào runner/trainer TV4, weighted loss, batch cuối, validation no_grad, early stopping/restore |
| 6 | Research/diagnostic checkpoint, fingerprint/config/provenance/checksum/run/seed và strict reload |
| 7 | Smoke AAPL5 epoch seed42, best2, finite gradients/weights/loss, coverage và reload exact |
| 8 | Lock phương ánA,3 research runs,146/300 epoch, mean/std mẫu và cả3 best checkpoints |
| 9 | Cùng250 validation dates,3CNN/3LSTM/persistence, USD MAE/RMSE và monitoring lỗi |
| 10 | Hướng dẫn setup/consumer, payload manifest/ZIP checksum và kiểm source tách riêng |

## Kiểm tra toàn thể

Bộ CNN/training/evaluation đạt162/162 tests, không skip, JUnit logs/audit/tv5_final_tests.xml. Giữ source TV1–TV3, trainer TV4 và notebooks TV1–TV4 theo protected hashes. Đúng một thay đổi protected có chủ đích là runner tích hợp CNN, hash được đăng ký ở TV5_Item6_Source_Changes.json. Official/comparison backend source hashes còn khớp bằng chứng lúc chạy.

Không phát hiện lỗi chặn phạm vi nghiệm thu local sau kiểm source và tests. Các điểm audit trước gồm lock config, câu README cũ và phụ thuộc artifacts/logs khi clone đã được xử lý lần lượt bằng official plan guard, cập nhật tài liệu và gói có dependency. Không coi dữ liệu/checkpoint tự khai metadata là bằng chứng thay thế logs đã đối chiếu.

CNN giữ cả3 seed42/123/456, best epochs32/41/43, validation MSE mean0,00805284/std0,00126121. Trên validation2023, persistence MAE/RMSE1,6368/2,1206USD thấp hơn LSTM mean2,2494/2,7511 và CNN mean3,3660/4,3507. Không sửa tuning để ép thắng baseline. Đây là bằng chứng nghiên cứu hợp lệ, không là kết luận test cuối hoặc lợi nhuận.

## Bàn giao và giới hạn

Hướng dẫn docs/TV5_Setup_and_Handoff.md. Gói chỉ rõ source/data/model dependencies, có3 selected CNN research,3 LSTM comparison và best smoke diagnostic; bỏ checkpoint intermediate dư thừa khỏi payload. Data/scaler/version/hash và log TV4 cần thiết được mang theo, vì Git source đơn thuần không chứa chúng. Mỗi file có hash và ZIP có sidecar checksum, không upload/push/merge trong tác vụ này.

Verifier dùng nguồn tách riêng và venv sạch đã có, kiểm hash/import/version lock/tests, forward toàn train/validation, reload6 models và tái tính USD metrics/monitoring. Không train lại AAPL từ đầu trong verifier; không tuyên bố fresh dependency install, máy người nhận hoặc hệ điều hành khác đã được xác nhận.

Kiểm source tách riêng đã đạt162/162 tests, forward và reload6 models, tái tính7 dòng metric USD khớp workspace gốc trong dung sai1e-12, dựng monitoring thành công. Module imports xác nhận từ root tách riêng, môi trường sạch/version lock đúng. Receipt logs/audit/tv5_item10_precheck.json. Lượt verifier đầu có lỗi đọc schema receipt forward, đã sửa verifier và chạy lại trọn vẹn; không ghi nhận lượt lỗi là đạt. Không sửa source model/training để hợp thức hóa lỗi.

Test2024–2025/multi-step final evaluation, API/release và hoàn thiện demo toàn hệ thống vẫn thuộc TV6. Peak RAM lịch sử, production drift/alerting/live TensorBoard CNN chưa đo/triển khai. Các phần quyền phân phối dữ liệu, lịch/deadline chung còn mở theo tài liệu project, không tự điền thay nhóm. TV5 hoàn thành local không có nghĩa toàn bộ10 mục đăng ký và7 nhóm báo cáo toàn project đã hoàn thành.

Gói cuối và receipt mới nhất được chỉ bởi logs/audit/tv5_item10_latest.json. ZIP là artifact local, không đưa vào Git. Cần người nhận chạy verifier để xác nhận acceptance trên máy họ.
