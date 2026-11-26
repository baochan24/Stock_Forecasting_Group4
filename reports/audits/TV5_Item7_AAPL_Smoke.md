# TV5 mục 7 — smoke CNN trên AAPL

Ngày 26/11/2026. Chạy chẩn đoán tối đa 5 epoch với seed 42 trên đủ 1.954 mẫu train và 250 validation, cùng data/scaler/prepared với LSTM đối ứng. Đây là giới hạn smoke do agent chọn trong phạm vi mục 7, không thay max100/ba seed của thực nghiệm chính thức.

Giữ kiến trúc phương án A, Adam 0,001, MSE, batch32, CPU float64, một Torch thread. Patience10 giữ nguyên nhưng không thể kích hoạt trong 5 epoch; early stopping đã được kiểm riêng bằng plateau tổng hợp. Không đánh giá hiệu năng test và không tuning từ kết quả smoke.

## Kiểm chứng thực tế

Script run_tv5_smoke.py gọi run_experiments chung TV4 với checkpoint_purpose diagnostic. Hooks chỉ quan sát số batch/mẫu, validation grad mode và gradient hữu hạn, không thay loss hoặc cập nhật weights. Trainer kiểm finite loss/gradients/weights mỗi batch. Sau run yêu cầu trọng số đã đổi, coverage đủ toàn bộ train/validation, giữ batch cuối.

Nạp best checkpoint bằng expected provenance/config fingerprint/run/seed từ caller. Loader mặc định phải từ chối diagnostic. Khi allow_diagnostic=True, instance mới phải khớp từng prediction validation với model best trong RAM bằng dung sai 0 và MSE bằng best_val_loss trong dung sai float64. Baseline YAML và hai manifest scaler/prepared được đối chiếu hash trước/sau.

Thời gian process CPU và wall được đo quanh runner, bao gồm checkpoint I/O và metadata; thời gian training loop đo riêng trong trainer. Không coi các số này là benchmark chính thức hoặc cam kết hiệu năng máy khác. Không lưu optimizer state để resume.

Notebook bổ sung bảng epoch, gradient/coverage/timing và biểu đồ loss, thời gian mỗi epoch, prediction chuẩn hóa và sai khác reload. Prediction plot chỉ phục vụ sanity, chưa là bằng chứng chất lượng hoặc vượt baseline. Outputs/weights/logs lưu local trong logs/audit/tv5_item7_*, không đưa vào Git.

## Kết quả thực thi

Run đạt đủ 5 epoch. Best validation MSE trên giá chuẩn hóa 0,054332359126796244 tại epoch 2; MSE sau reload bằng đúng giá trị đó, mọi prediction validation khớp model RAM với dung sai 0. Loader mặc định đã từ chối diagnostic. Trọng số thay đổi và hữu hạn, không thay data manifests hoặc baseline YAML.

| Epoch | Train MSE | Validation MSE |
|---|---:|---:|
| 1 | 0,601709 | 0,420335 |
| 2 | 0,164466 | 0,054332 |
| 3 | 0,021513 | 0,069751 |
| 4 | 0,030540 | 0,150875 |
| 5 | 0,030825 | 0,105344 |

Đây là bảng hiển thị làm tròn, CSV và receipt giữ đầy đủ precision. Validation tăng sau epoch 2, chưa kết luận overfit từ run ngắn. Không đổi learning rate hoặc kiến trúc dựa vào smoke.

Hooks ghi 310 train batches và 40 validation batches, tương ứng 9.770/1.250 lượt mẫu qua 5 epoch; đây vẫn là 1.954/250 mẫu duy nhất. Có 2.480 lượt tensor gradient hữu hạn, max abs gradient 5,19484148401887; validation không bật grad. Train/validation tail 2/26 mẫu đều được giữ.

Training loop mất 1,8162 giây; runner wall 7,0235 giây, process CPU 4,53125 giây trong điều kiện một Torch thread tại máy local. Các số đo không gồm thời gian preflight nạp loader trước runner. Python 3.13.7, PyTorch 2.14.1+cpu.

Receipt tại `logs/audit/tv5_item7_20261126T043358119493Z/summary.json`, history.csv, validation_scaled.csv, smoke.yaml và smoke_overview.png cùng thư mục. Checkpoint tốt nhất nằm trong thư mục checkpoints của run diagnostic này. Notebook local có 19 cells và 11/11 code cell đã thực thi, giữ các output trước. Receipt notebook ở notebook_verification.json cùng thư mục.

Bước tiếp theo theo flow là mục 8; trước chạy cần khóa/fingerprint phương án A, ngân sách và ba seeds đã chốt. Smoke đạt kỹ thuật local, chưa phải model chính thức hoặc kết quả so sánh CNN/LSTM/persistence.
