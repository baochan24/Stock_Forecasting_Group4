# experiments/runner

Từ TV5 mục 6, runner dispatch saver CNN riêng và cho persist_checkpoint=True khi loader có provenance. checkpoint_purpose='diagnostic' dùng cho smoke/diagnostics, research cho thực nghiệm chính thức. RAM mode vẫn dùng persist_checkpoint=False. CNN thiếu provenance bị từ chối trước backward. LSTM giữ saver hiện có, trainer không thay đổi. Nội dung mục 5 bên dưới là lịch sử trước khi nối saver CNN.

TV5 mục 5 thêm cnn_factories.py, YAML cnn_one_step_baseline.yaml và dispatch CNN trong runner. Cấu hình dữ liệu được chuyển schema sang reference LSTM chỉ để gọi lại loader đã kiểm chứng, không đổi arrays hoặc tạo LSTM để train. CNN dùng train_model/_run_epoch chung. Trong mục 5, gọi run_experiments với persist_checkpoint=False để diagnostic RAM; persistence CNN bị từ chối trước tạo run cho tới mục 6. Không dùng saver LSTM cho CNN.

TV5 mục 3 thêm cnn_data.py với make_cnn_comparison_loaders. Hàm nhận cấu hình dữ liệu LSTM đối ứng đã khóa và trả cùng train/validation loaders, giữ shape (B,30,1), y (B,1), ID/ngày/provenance. Việc tạo model và training CNN sẽ nối ở các mục sau.

Điều phối pipeline nghiên cứu theo cấu hình. Không phục vụ yêu cầu web.

TV4 mục1: experiment_runner.py nhận từ PR#10, đặt đúng module này thay vị trí management trên nhánh gốc, giữ nguyên nội dung. Import `backend.experiments.runner.experiment_runner`; run_experiments nhận factories từ caller.

Từ mục 3, runner mặc định dùng `make_aapl_model` và `make_aapl_loaders` trong `aapl_factories.py`. Hai YAML trong experiments/configs ghim snapshot cùng hash manifest scaler và prepared. Mỗi batch cung cấp X, y và sample IDs theo thứ tự phiên. Dataset cũng giữ ngày gốc dự báo, ngày target và nguồn artifacts. Chi tiết chạy kiểm tra trong docs/TV4_Setup_and_Reproduce.md.
