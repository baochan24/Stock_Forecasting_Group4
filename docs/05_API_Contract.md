# Interface/API — bản thiết kế đã chốt

Mục8 đã triển khai local27/11/2026 bằng FastAPI/Uvicorn. Tiền tố /api/v1, release lịch sửaapl-research-residual-v1. Dùng release_id, không gọi toàn hệ thống là demo. Xem [hướng dẫn API thực tế](TV6_API_Setup_and_Contract.md); các chi tiết dưới được giữ làm hợp đồng nền.

| Method | Path | Trách nhiệm |
|---|---|---|
| GET | /releases/current | Release hiện tại |
| GET | /releases/{release_id} | Thông tin, dataset/model và khả năng hỗ trợ |
| GET | /forecast-origins | Ngày gốc hợp lệ theo release/chế độ |
| GET | /datasets/{dataset_version}/prices | Chuỗi giá trong phạm vi giới hạn |
| POST | /predictions | Inference và baseline |
| GET | /results | Kết quả đã lưu |
| GET | /metrics | Metric chính thức hoặc khoảng chọn |
| GET | /experiments/{run_id} | Cấu hình, loss, checkpoint |
| GET | /experiments/{run_id}/audits | Audit và bằng chứng |
| POST | /model-traces | Truy vết inference hỗ trợ |
| GET | /health | Tiến trình API |
| GET | /readiness | Bộ phát hành sẵn sàng |

Request predictions: release_id, forecast_origin, forecast_length (1 hoặc 5), methods.
Một bước: lstm/cnn/persistence; năm bước: lstm/persistence. Không nhận target, scaler, checkpoint path từ client.
Response: request_id, release_id, dataset_version, result_source; status complete/partial/failed; input/context; status từng phương pháp; prediction theo horizon/date; comparison riêng nếu có target.
Persistence không có checkpoint; có phiên bản quy tắc. Phương pháp lỗi phải ghi rõ; không coi partial là so sánh chính thức đầy đủ.

Results đọc bộ đã lưu; predictions chạy inference. Metric lọc theo forecast_origin, trả phạm vi/số mẫu/horizon. Không trộn release hoặc metric từ run khác.
Danh sách cần phân trang/giới hạn. Mức giới hạn cụ thể chốt sau đo; trace giới hạn chi tiết.
Training trace đọc bản ghi, không cập nhật trọng số web. Minh họa gắn nhãn, không giả làm phép tính thật.

HTTP: 422 yêu cầu không hợp lệ; 404 release/dataset/run không có; 503 release chưa sẵn sàng/không tương thích; 500 lỗi ngoài dự kiến. Response lỗi gồm request_id, error.code, error.message, details phù hợp; traceback/đường dẫn nội bộ chỉ trong log.
Health và readiness tách biệt. Không có API train trong phạm vi hiện tại.
