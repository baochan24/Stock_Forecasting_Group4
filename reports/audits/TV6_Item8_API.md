# TV6 mục 8 — nghiệm thu API

**Hoàn thành local ngày 27/11/2026.** Đã triển khai 12 route theo contract `/api/v1` bằng FastAPI/Uvicorn. Chưa triển khai frontend; không train hoặc thay trọng số.

## Tái audit 27/11/2026 — kết quả hiện tại

Phát hiện và sửa hai thiếu sót: mẫu Swagger mặc định dùng `string` làm ngày nên không thể chạy ngay; metric chưa kiểm actual giữa các phương pháp hoặc keys trùng. Mẫu request nay dùng phiên thật `2023-06-15`; metric từ chối cohort trùng, thiếu hoặc actual khác nhau. Dữ liệu hiện tại không có các lỗi cohort này; đây là bổ sung kiểm soát, không thay kết quả mô hình.

- **51 tests passed**, 2 warnings deprecation; gồm chạy được cả mẫu Swagger prediction/trace và kiểm cohort lỗi.
- **15 HTTP checks passed** qua server Uvicorn riêng port 56074, đã dừng; không dừng server người dùng trên port 8000.
- **20.144 dòng** được đối chiếu với snapshot 2.766 dòng: actual, phiên target, error, finite và keys duy nhất đều đạt.
- MAE/RMSE của **12 nhóm horizon/seed/split** được tính lại bằng scalar math và khớp; tất cả hash release/sidecar vẫn hợp lệ; 69 package core khớp; pip check đạt.
- Notebook cập nhật trực tiếp: **48 cells, 24 code cells**, chạy lại 3 cell API liên quan; giữ output các mục trước. Builder đã đồng bộ.

Bằng chứng mới: `logs/audit/tv6_item8_20261127T085021938193Z/` gồm summary, acceptance, data_reaudit, HTTP responses/checks, notebook_verification. JUnit: `logs/audit/tv6_item8_reaudit_tests.xml`. Chạy lại kiểm dữ liệu bằng `.venv/tv4_clean/Scripts/python.exe scripts/audit_tv6_api_data.py` sau HTTP checker và pytest tương ứng.

Kết luận: chưa phát hiện lỗi chặn trong phạm vi API demo local đã kiểm. Không khẳng định không thể còn lỗi; chưa load test, triển khai Internet hoặc xác nhận máy khác. ZIP mục 7 chưa chứa API/sidecar mới, cần xử lý khi bàn giao mục 10. Sau thay source, dừng server cũ bằng Ctrl+C và chạy lại script API để Swagger nạp mẫu mới; reload trang `/docs`.

Các số liệu 46 tests/46 cells bên dưới là lần nghiệm thu ban đầu, được giữ để truy nguyên lịch sử.

## Thành phần và hành vi

- `backend/api/app.py`, `schemas.py`: HTTP, kiểm tra request, request ID, CORS, xử lý lỗi và OpenAPI.
- `backend/services/forecast_service.py`: kiểm release/readiness, tạo input từ snapshot, gọi ReleaseForecaster, ghép comparison sau inference và điều phối trace TV3.
- `backend/services/results/release_results.py`: đọc kết quả/thí nghiệm đã lưu, gọi Evaluation trên cùng cohort. Không forward khi đọc results/metrics.
- `scripts/build_tv6_api_data.py`: sidecar chỉ đọc gồm 20.144 dòng dự báo và history/config của 9 thí nghiệm, gắn với release SHA và hash từng file.
- `scripts/run_tv6_api.py`: bind `127.0.0.1:8000`, một worker. HTTP checker khởi chạy server riêng và tự dừng đúng process đó sau kiểm tra.

Không sửa mã/model đã pin trong release mục 7. Các module API/service được thêm riêng. Release SHA vẫn là `a4b04a50c3e499b95407a5a8f9de379a40f6371bbb532cc01df90fdb2b5719a3`.

Các endpoint gồm health/readiness; release current/detail; forecast origins; dataset prices; predictions; results/metrics; experiments/history/audits; model traces. Health độc lập với artifacts; readiness kiểm integrity và nạp thử đủ 9 model trước khi báo ready.

Client chỉ gửi release, origin, horizon, methods và seed. Không nhận target, scaler hoặc checkpoint path. Seed42 là mặc định cố định, cả ba seed được hỗ trợ. Inference phải trả đủ method/horizon mới được báo complete; thiếu đầu ra trả 503. Actual/error nằm trong comparison riêng, không truyền vào model.

Stored results có nguồn và evaluation phase rõ ràng. Metrics phân biệt full split với selected range, giữ cùng keys giữa các phương pháp, báo đúng số mẫu/sai số và h5 overall. Trả seed được chọn, không ngầm thay bằng mean ba seed nghiên cứu. Trace LSTM được tái tính và đối chiếu số học; giá USD sau decode khớp inference.

## Bằng chứng

| Kiểm chứng | Kết quả |
|---|---|
| Bộ kiểm tra cuối | **46 passed**, 40,84 giây |
| HTTP thực | **15 checks passed**, 19,39 giây gồm startup |
| Model core | 69 package vẫn khớp TV4 lock |
| pip check | Không có dependencies bị hỏng |
| Weights/release | Hash giữ nguyên; không train/refit |
| Notebook | 46 cells, 23 code cells có output |

Các ca kiểm tra bao phủ h1/h5, ba seed và hai origin khớp ReleaseForecaster; input/schema/ID sai; health khác readiness; lỗi 404/422/503/500 được làm sạch; CORS cả khi lỗi 500; không báo complete khi thiếu output; metrics so với scalar math trên cùng range; pagination; experiment/audit; trace summary/full; không fit và không có train endpoint.

HTTP checker gọi đủ nhóm route qua Uvicorn trên localhost, kiểm request ID khớp header, dự báo h1/h5, trace verified, lỗi 404 và 422. Port55372 là phiên kiểm tra tạm đã dừng, không phải server đang được giữ chạy.

Receipt: `logs/audit/tv6_item8_20261127T033804495431Z/summary.json` và `acceptance.json`. Cùng thư mục có checks, HTTP responses, server log, biểu đồ và notebook verification. JUnit: `logs/audit/tv6_item8_final_tests.xml`. Environment evidence: `logs/audit/tv6_api_environment.json`. Request logs: `logs/api/requests.log`.

Dependencies API được cài với constraints TV4, không thay các phiên bản core. Lock API bổ sung 16 package. Hai warning deprecation của anyio/Starlette TestClient được giữ trong log; không phải test failure và không nâng thư viện core để che warning.

## Giới hạn và bàn giao

API phục vụ snapshot lịch sử, target2023–2025; không live, ticker khác hoặc giao dịch. API hoạt động đúng không làm tăng độ chính xác hay tính độc lập của kết quả mô hình. Trace là snapshot inference có kiểm chứng, không phải log gradient huấn luyện.

Sidecar API là artifact mới; ZIP mục 7 đã khóa chỉ phục vụ inference và chưa có API mới. Workspace hiện có đủ dữ liệu để chạy. Bàn giao sang máy khác cần cả sidecar, source API và dependencies; kiểm chứng đó thuộc mục 10. Chưa load test, deployment Internet hoặc triển khai frontend. Không upload/push Git trong bước này.

Mục 8 đạt phạm vi được giao. [Cách chạy và schema](../../docs/TV6_API_Setup_and_Contract.md). Bước tiếp theo là mục 9: frontend AAPL Forecast Lab theo concept đã chốt.
