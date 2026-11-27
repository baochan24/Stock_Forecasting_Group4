# TV3 — bàn giao kiến trúc/trace cho TV4 và TV6

Đây là bàn giao source/contract đã kiểm chứng local, **không có checkpoint huấn luyện AAPL chính thức**. Hai model CPU float64, không thay TV2 snapshot/scaler/prepared. Xem TV3_Setup_and_Reproduce.md để tạo venv sạch và TV3_Progress.md để biết trạng thái.

## TV4 nhận gì và làm gì tiếp?

```python
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.data.preparation.tensors import make_lstm_training_batch

# batch/scaler/version phải được load và verify từ TV2 trước.
model = LSTMOneStep().cpu()   # LSTMMultiStep() cho5 outputs, trọng số riêng
tensors = make_lstm_training_batch(batch, scaler, dataset_version=version, forecast_length=1)
prediction = model(tensors['X'])  # Chỉ X; y chỉ dùng trong loss bên ngoài model
```

Input/target float64, X=(B,30,1), y=(B,1)/(B,5). Không dùng .float() hoặc autocast/AMP trong cấu hình hiện tại. Mỗi forward h/c0 mới, không carry state giữa mẫu. TV4 viết loop Adam/MSE, validation/early-stopping và chọn checkpoint bằng validation theo thiết kế; giữ batch cuối và log epoch loss theo số mẫu. Không chọn cấu hình/seed bằng test. Model1/5 train và checkpoint riêng.

Module artifacts/lstm_checkpoint.py chỉ lưu/nạp, không quyết định lúc train/save. `save_lstm_checkpoint(model, output_root, checkpoint_id, metadata, lookback=30)` yêu cầu weights CPU float64 hữu hạn và ID mới. Metadata gồm dataset_version,5 source_hashes,scaler_id,run_id,trained(bool). Nếu trained=True cần selected_on='validation',best_epoch>=1. Caller TV4 chịu tính trung thực/history của các trường này; JSON không chứng minh model thật sự đã được train. Bổ sung validation loss/seed/config/run logs theo pipeline thực tế, không tự gắn nhãn trained cho weights khởi tạo.

`weights.pt` chỉ state_dict, manifest.json ghi config/model/horizon/lookback/dtype/hash và metadata. Fail giữa ghi có thể để thư mục dở, retry ID mới; không nhận nếu thiếu manifest. Không ghi đè run cũ. Chưa có checkpoint nghiên cứu để cung cấp; tests chỉ dùng diagnostic trained=False trong thư mục tạm.

## TV6 nhận gì và điều kiện inference?

```python
from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint
from backend.data.preparation.tensors import make_lstm_inputs
from backend.model_trace import trace_lstm

# Khi TV4 đã bàn giao checkpoint thật + scaler đúng bộ:
model, manifest = load_lstm_checkpoint(
    checkpoint_folder,
    expected_dataset_version=version,
    expected_source_hashes=accepted_hashes,
    expected_scaler_id=scaler_id,
    expected_forecast_length=1,
    expected_lookback=30,
)
inputs_only = make_lstm_inputs(records, scaler, dataset_version=version, forecast_length=1)
# torch.inference_mode() cho forward thông thường; trace tự dùng no_grad.
trace = trace_lstm(model, inputs_only['X'][:1])
```

Loader trả eval/CPU/float64; kiểm version/source/scaler/model/horizon/lookback/hash và actual state dtype trước strict load, không silent cast weights32→64. Nạp weights_only=True. Mặc định từ chối trained=False; allow_diagnostic=True chỉ dùng tests/giải thích kỹ thuật, không phục vụ dự báo như model đã train. Checksums là nhất quán local, không xác thực tác giả; chỉ nhận file tin cậy.

Output model/trace vẫn ở thang chuẩn hóa, inverse bằng scaler train trước khi hiển thị USD/metric. Inference không nhận target hoặc cập nhật weights. Raw record/version/origin/target dates/horizon theo docs/04, không ghép chỉ bằng target_date. Trace chỉ một sample; schema/gates reconstructed-and-verified xem TV3_Trace_Contract.md, còn cần TV6 thống nhất trước đưa lên API. Không gán giải thích kinh tế cho hidden/gate. Không tự triển khai API/frontend ở TV3.

## Gói và xác nhận nhận bàn giao

Gói `TV3_Handoff_<run>.zip` + `.sha256` trong artifacts/releases gồm source chọn lọc/tests/lock/docs/notebook và artifacts TV1/TV2 cần kiểm chứng, **trained_checkpoints=[]**. Không .git/.venv/secrets/model đã train. Tên gói là source/contract handoff, không release phục vụ dự báo. Không tự upload/push/gửi thành viên khác.

Giải nén thư mục mới, so SHA ZIP, tạo venv sạch theo lock, chạy `scripts/verify_tv3_handoff.py`. Verifier kiểm checksum, tests --require-clean, integration và trace. Notebook protected theo hash cell sources (không hash outputs) để Run All không bị xem là sửa source; logs/output mới không thay manifest nguồn. Sau verify có thể mở/chạy notebook hoặc build lại đúng source đã đóng gói.

TV4 xác nhận import/forward/loss dtype64 và checkpoint contract; TV6 xác nhận loader/inverse/input-only/trace schema cần thiết. Người nhận ghi người/máy/OS/Python/ZIP SHA/lock hash/log IDs/kết quả. Chưa được nhận xác nhận thì giữ recipient_machine_verified=false,checkpoint_training_verified=false; không báo hoàn thành thay người khác. Các bước training thực nghiệm và checkpoint chính thức thuộc TV4; TV3 đã cung cấp ranh giới kỹ thuật và tiếp tục hỗ trợ khi có artifacts thật.
