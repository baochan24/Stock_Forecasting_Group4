# experiments/runner

Điều phối pipeline nghiên cứu theo cấu hình. Không phục vụ yêu cầu web.

TV4 mục1: experiment_runner.py nhận từ PR#10, đặt đúng module này thay vị trí management trên nhánh gốc, giữ nguyên nội dung. Import `backend.experiments.runner.experiment_runner`; run_experiments nhận factories từ caller.

Từ mục 3, runner mặc định dùng `make_aapl_model` và `make_aapl_loaders` trong `aapl_factories.py`. Hai YAML trong experiments/configs ghim snapshot cùng hash manifest scaler và prepared. Mỗi batch cung cấp X, y và sample IDs theo thứ tự phiên. Dataset cũng giữ ngày gốc dự báo, ngày target và nguồn artifacts. Chi tiết chạy kiểm tra trong docs/TV4_Setup_and_Reproduce.md.
