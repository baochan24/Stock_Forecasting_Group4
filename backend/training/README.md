# training

Giao diện hiện tại yêu cầu callback callable `checkpoint_saver(model, epoch, val_loss)` khi truyền `checkpoint_dir`. Thiếu callback được từ chối trước khi tạo thư mục hoặc cập nhật trọng số. Dùng `checkpoint_dir=None` để chọn best trong RAM, hoặc gọi `run_experiments` để lưu LSTM với provenance. Helper import `backend.artifacts.save_checkpoint` cũ đã được loại bỏ.

Mục 5 bổ sung callback `checkpoint_saver(model, epoch, val_loss)` cho mỗi lần validation cải thiện. Runner dùng `save_lstm_checkpoint` của artifacts, tạo ID riêng theo run và epoch. Kết quả trainer trả đường dẫn thư mục best. `persist_checkpoint=False` vẫn dùng lựa chọn trong RAM cho phép thử mục 4.

Training/validation, early stopping, chọn checkpoint. Quyết định lúc lưu; artifact module thực hiện lưu. Không phụ thuộc API.

TV4 mục1: đã nhận `trainer.py` và export `train_model` từ PR#10 commit16555929210314b1eb06da9dc84b827ececc1b9e, giữ nguyên nội dung. Tests dùng tensors tổng hợp và mock checkpoint; xem reports/audits/TV4_Progress.md.

Mục2: loop giữ nguyên dtype input/target, yêu cầu khớp dtype model và CPU; hai LSTM TV3 bắt buộc float64, một feature, target đúng horizon1/5. Input mặc định(B,30,1), hỗ trợ shape10/60 theo kế hoạch; không tự cast/migrate model hoặc thay global dtype. Model tổng hợp khác vẫn dùng dtype tham số của chính model, chưa chốt dtype CNN.

`scripts/check_tv4_float64.py` kiểm cập nhật Adam và bước validation trên tensor tổng hợp. Với dữ liệu AAPL, dùng `scripts/check_tv4_aapl_data.py` để kiểm batch CPU float64 của hai cấu hình LSTM. Việc lưu và nạp checkpoint thật thuộc mục 5.

Mục 4 kiểm tra gradient sau backward và trọng số trước khi chạy từng epoch và sau mỗi bước Adam. Validation dùng eval/no_grad. Mỗi batch đóng góp vào MSE của epoch theo số mẫu thực tế. Trainer giữ bản sao trọng số khi validation MSE giảm nghiêm ngặt, đặt lại bộ đếm patience rồi phục hồi bản tốt nhất vào model cuối run. Tham số `checkpoint_dir=None` chọn lưu trong RAM cho phép thử này.
