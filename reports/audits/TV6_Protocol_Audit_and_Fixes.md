# TV6 — audit các điểm khóa và sửa guard

Ngày26/11/2026, thực hiện theo yêu cầu người dùng. Đối chiếu rule/đề/decision log/contract và code thực. Không inference/model metric test, không đổi model hoặc cohort sau kết quả test.

## Phát hiện và sửa

| Phát hiện | Ảnh hưởng tiềm tàng trước sửa | Sửa/kiểm chứng |
|---|---|---|
| Guard intake dùng assert; format_version so bằng equality | Python -O bỏ assert; bool/float có thể qua kiểm format1 | Explicit ValueError, kiểm kiểu int/schema; test -O và malformed types |
| Path và membership các references chưa đủ chặt | Inventory sai có thể dẫn ngoài root hoặc dùng file không được pin | Resolve dưới root, từ chối absolute/backslash/.., bắt mọi reference nằm trong bảng hash |
| Models/cohorts dựa nhiều vào intake khai báo | Thiếu kiểm độc lập duplicate checkpoints/run, manifest linkage và full eligible dates | Ràng buộc9 unique checkpoints/runs, manifest/config/run/seed/epoch/data/scaler; source date enumeration/history/mode/ID |
| Chưa có anchor lifecycle riêng của lock | File lock mất có thể bị tạo lại như lần đầu, receipt at-lock chưa phải dấu vết đầy đủ | Registry bytes/fingerprint và prior receipt, explicit adoption, chặn mất lock/cả registry khi có history |

Không phát hiện model/scaler/data bàn giao bị hỏng. Các phát hiện là thiếu độ chặt của validator/lifecycle, không phải bằng chứng đã có test leakage hoặc metric sai. Những lựa chọn nghiên cứu được giữ nguyên: seeds42/123/456,lookback30,9 checkpoint,502/498 test cohorts,MAE/RMSE USD/per-horizon/std ddof1,rolling20/top10 vàdemo seed42 minh họa cố định. Demo seed42 không được coi tốt nhất. Numeric tie không là practical/statistical significance.

## Bằng chứng

45/45 tests evaluation/protocol đạt, gồm28 tests protocol và17 tests metric/monitoring. Có ca rehash policy vẫn bị từ chối, Python -O, unsafe/unpinned paths, duplicate references, schema/types, registry sai/mất, prior receipt hỏng, mất cả lock/registry còn history. Tests dùng fixtures tạm hoặc monkeypatch in-memory, không sửa artifacts thật. JUnit logs/audit/tv6_protocol_audit_tests.xml.

File protocol v1 giữ nguyên từng byte so bản lưu trước sửa. Raw file SHA256 c5a6debc373d3e53a13bddcf1a50242514d5ae4d4a58c5a57d5ff97b621e987a. Semantic SHA256 vẫn9e81b5ca4f3ae9ddfd5969d846458afbf87e95ea89be98ddb8349a4906119579. Registry mới đăng ký tại thời điểm audit, không giả thời gian đăng ký là lúc tạo v1. Verify chạy lại không đổi bytes lock/registry.

Receipt logs/audit/tv6_protocol_audit_20261126T164022898092Z/summary.json ghi hashes code/tests/lock/registry và phạm vi. Bản source trước sửa tại logs/audit/tv6_protocol_audit_before. Không ghi đè các receipt cũ.

## Giới hạn còn lại đúng flow

Registry local không là digital signature hoặc chứng minh không ai đã chạy test ngoài workflow. Final evaluator/inference chưa triển khai trong mục2, cần gọi guard mặc định và ghi protocol/run identity ở các mục3–5. Không tuyên bố hệ thống đã có end-to-end enforcement từ việc validator đạt tests. Hash không thay thế xác thực nguồn Yahoo; point-in-time/adjustment và search-budget limits giữ nguyên.

Audit đạt phạm vi local, không còn phát hiện chặn mục3 sau sửa trong các điểm đã kiểm. Notebook06 bổ sung bảng audit riêng; các mục3–10 vẫn chờ theo flow.
