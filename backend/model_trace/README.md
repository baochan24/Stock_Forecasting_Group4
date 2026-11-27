# model_trace

`gradient_diagnostics.py`: chẩn đoán backward trên bản sao LSTM CPUfloat64, không optimizer/update caller. Trả norm core/head/input theo mean-scaledMSE, không phải logoptimizer hoặc schema traceAPIv1. Caller chỉ truyền batchtrain trong kiểmTV6; xem reports/audits/TV6_LSTM_Learning_Check.md.

TV3 mục5: trace đã tái kiểm chứng6 stages trong bản source/artifacts độc lập dùng `.venv/tv3_clean`, lock68 packages, không source từ môi trường audit. Tất cả đạt; xem reports/audits/TV3_Environment_Reproduce.md. Không đổi schema/tolerance/thuật toán ở mục5, không training hoặc API approval.

**Mục4 hoàn thành local23/11/2026:** suite89/89 đạt, trace sau Adam tổng hợp và state_dict/JSON roundtrip khớp, không đổi weights/gradients/input/mode. Float64 hiện dùng rtol1e-10/atol1e-12; số1e-5/1e-6 trong lịch sử bên dưới chỉ còn fallback32. Schema/điều kiện/giới hạn chi tiết tại docs/TV3_Trace_Contract.md, chưa là API chính thức TV6. Notebook TV3 mục4 có bảng/gate plots/output thật. CLI check_tv3_trace.py ghi6 traces trên input TV2 thật với weights khởi tạo/synthetic-step, không checkpoint đã train; evidence TV3_Progress.md.

Cập nhật precision23/11/2026: mặc định model/input float64, trace kế thừa dtype từ model/x nên không đổi công thức. Tests trace và lưu/nạp float64 đạt; benchmark max hidden/cell abs error khoảng5.55e-17, nhỏ hơn dung sai hiện tại rtol1e-5/atol1e-6. Chưa tự thay trace schema/API hoặc chốt nghiệm thu mục4; xem TV3_Progress.md.

Truy vết inference hoặc batch đại diện. Phân biệt phép tính thật/minh họa; không tự cập nhật model phục vụ web.

Trạng thái 23/11/2026: đã tiếp nhận lstm_trace.py/__init__.py đúng module từ commit `1f209b70c5690fb5e41b3b26d8eab36b2b6c029d`, giữ source tác giả. Import `from backend.model_trace import trace_lstm` từ gốc project hoạt động, suite55/55 đạt local.

`trace_lstm(model,x)` cần model.eval(), x một cửa sổ `(1,T,1)` đúng dtype model, không target. Tái dựng gate i/f/g/o từ trọng số thực, đối chiếu hidden/cell/forward với rtol1e-5/atol1e-6, chỉ trả trace khi đạt. Không fit/train/đổi weights, có no_grad. Đây là reconstructed-and-verified trace, không phải gate tensor hook trực tiếp từ kernel, không giải thích nguyên nhân thị trường.

Schema trace nội bộ chưa là API TV6 đã duyệt. Mục 4 TV3 sẽ nghiệm thu trace đầy đủ, gồm model lưu/nạp; không coi việc tiếp nhận/chạy tests ở mục 1 là hoàn thành trace bàn giao toàn hệ thống.
