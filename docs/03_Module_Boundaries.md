# Module boundaries

- `backend/data/acquisition/`: Tải dữ liệu và metadata nguồn. Giữ bản gốc; ghi chính sách điều chỉnh và hash.
- `backend/data/validation/`: Kiểm tra ngày, thiếu/trùng, giá trị; trả báo cáo và dữ liệu hợp lệ. Dùng chung phép kiểm tra với audit.
- `backend/data/preparation/`: Chia tập, fit scaler train, tạo mẫu kèm ngày/split. Không fit scaler khi inference.
- `backend/data/transforms/`: Phép chuẩn hóa, inverse transform, tạo cửa sổ dùng chung. Không tự fit lại scaler.
- `backend/models/lstm_one_step/`: LSTM một lớp hidden 32, Linear ra 1 là cấu hình khởi đầu. Định nghĩa mạng và forward.
- `backend/models/cnn_one_step/`: CNN 1D một bước; kiến trúc cụ thể còn mở. Giữ đúng ý nghĩa input và target.
- `backend/models/lstm_multi_step/`: LSTM hidden 32, Linear ra 5; direct multi-output, checkpoint riêng.
- `backend/baselines/`: Persistence dùng giá gốc cuối input. Một bước ra một giá; năm bước lặp lại cùng giá đó. Không training.
- `backend/training/`: Training/validation, early stopping, chọn checkpoint. Quyết định lúc lưu; artifact module thực hiện lưu. Không phụ thuộc API.
- `backend/inference/`: Điều phối input, model/baseline và khôi phục giá. Không nhận target, không cập nhật trọng số.
- `backend/evaluation/`: Căn target, sai số, MAE/RMSE, số mẫu và horizon. Sở hữu phép tính metric dùng chung.
- `backend/error_analysis/`: Phân nhóm, chọn ví dụ theo quy tắc, diễn giải kết quả Evaluation. Không viết lại metric.
- `backend/model_trace/`: Truy vết inference hoặc batch đại diện. Phân biệt phép tính thật/minh họa; không tự cập nhật model phục vụ web.
- `backend/experiments/runner/`: Điều phối pipeline nghiên cứu theo cấu hình. Không phục vụ yêu cầu web.
- `backend/experiments/management/`: Run ID, seed, môi trường, logs và trạng thái. Không kiêm quyết định model thắng.
- `backend/artifacts/`: Lưu/nạp và kiểm tra liên kết dataset, scaler, cấu hình, checkpoint, kết quả/release. Không gọi ngược training.
- `backend/audit/`: Kiểm tra quy tắc xuyên giai đoạn; ghi đạt/không đạt và bằng chứng. Không âm thầm sửa dữ liệu.
- `backend/services/results/`: Cung cấp kết quả đã lưu hoặc metric khoảng chọn qua Evaluation, đúng release/run.
- `backend/api/`: Request/response, kiểm tra tham số, điều phối service, lỗi. Không có training endpoint, không nhân bản logic dự báo.

Front-end chỉ gọi API. Models/baselines/transforms không phụ thuộc training/API/front-end. API gọi inference/results/trace; các module này không gọi ngược API. Artifact Management không điều khiển training. Trace không gọi vòng qua inference/API.
