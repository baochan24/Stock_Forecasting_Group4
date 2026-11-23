# TV3 — hợp đồng trace nội bộ

Mục4 TV3,23/11/2026. Đây là schema implementation local, **chưa là API web được TV6 phê duyệt**. Không suy diễn nguyên nhân thị trường hoặc ý nghĩa kinh tế của chiều hidden/gate.

## Cách gọi

`trace_lstm(model,x)` từ backend.model_trace, chỉ nhận LSTMOneStep/LSTMMultiStep. Model/lstm/fc đều eval; x một cửa sổ `(1,T,input_size)`, thông thường `(1,30,1)`, hữu hạn và khớp dtype/device weights. Hiện mặc định CPU float64. Không nhận target, không chuẩn hóa/fit, không tự load checkpoint hoặc xác minh nguồn; caller phải làm trước.

Tái dựng gates i/f/g/o từ weights và hai bias PyTorch; c=f*c_previous+i*g, h=o*tanh(c). So h/c từng phiên với nn.LSTM từng bước, hidden sequence/state cuối với nn.LSTM cả chuỗi, Linear output với forward model. Gate là phép tính tái dựng được đối chiếu, không hook trực tiếp từ kernel. Mismatch/nonfinite state/output báo lỗi, không trả trace chưa kiểm chứng.

Dung sai float64: **rtol1e-10/atol1e-12**. Nếu caller chủ động chuyển model/input thành float32, fallback vẫn1e-5/1e-6; không phải mặc định project. Verification ghi đúng dung sai sử dụng.

## Schema trả về

| Trường | Ý nghĩa |
|---|---|
| trace_type | reconstructed_and_verified |
| input_shape / output_shape | [1,T,input_size] / [1,H], H1/5 |
| input_scaled | T×input_size, giá chuẩn hóa |
| prediction_scaled | H output chuẩn hóa, chưa là USD |
| initial_hidden / initial_cell | Vector0 hidden_size, mặc định32 |
| steps | T records theo time_step1..T |
| linear_input | hidden vector cuối |
| verification | passed, rtol, atol và max_hidden/cell/prediction_abs_error |

Mỗi step có time_step, input_gate, forget_gate, candidate_state, output_gate, hidden_state, cell_state. Các vector dài hidden_size; i/f/o thuộc[0,1], candidate[-1,1]. JSON allow_nan=False. Core không thêm sample_id/date/version; CLI bọc identity/input_dates bên ngoài trace, không đưa target vào hàm.

## Tính chỉ đọc và bằng chứng

Không đổi mode/weights/input hoặc gradients có sẵn. No_grad không xóa grad đã có; tests kiểm điều này. Sau load đúng state_dict/input/dtype, trace bằng trước load trên CPU đã thử; không bảo đảm mọi nền tảng bitwise giống nhau.

Tests dùng một Adam step tổng hợp, file state_dict và trace JSON tạm. CLI check_tv3_trace.py nhận2 input train thật sau accept TV2, update model bằng synthetic_x/target0, không train AAPL hoặc tạo checkpoint nghiên cứu. Lưu6 trace JSON (2 model×3 stages initial/after_synthetic_step/after_reload) có checksums, giữ artifacts nguồn.

Lệnh: `.venv/tv3_review_env/Scripts/python.exe -X utf8 scripts/check_tv3_trace.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z --prepared-dir data/prepared/tv2_prepared_20261122T145943242978Z`.
