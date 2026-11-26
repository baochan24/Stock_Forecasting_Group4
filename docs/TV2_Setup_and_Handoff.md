# TV2 — setup, tái lập và bàn giao preprocessing

Phạm vi: source TV2 + dữ liệu TV1 cố định + scaler train + mẫu một/năm bước. Đây chưa phải release model đã train, không có checkpoint hoặc kết quả MAE/RMSE. Chuẩn Windows CPU/Python 3.13.7; chưa xác nhận nền tảng khác hoặc máy thành viên khác.

## 1. Nhận và kiểm tra gói

Gói local do `scripts/package_tv2_handoff.py` tạo: `artifacts/releases/TV2_Handoff_<run>.zip` và `.zip.sha256`. Không tự upload. Nhận nguyên ZIP và checksum từ người bàn giao; checksum đi cùng gói chỉ kiểm tra toàn vẹn, không phải chữ ký bên thứ ba. So `Get-FileHash -Algorithm SHA256 <zip>` với checksum, giải nén vào thư mục mới, không ghi đè project/run cũ.

ZIP có HANDOFF.json (hash từng file, version, scaler/prepared IDs và source Git head/dirty), source chọn lọc, tests, requirements lock, 5 artifacts TV1, scaler.json/manifest.json và hai mode prepared. Không chứa .git, .venv, secrets, model hoặc frontend. Source có thay đổi chưa commit được nhận diện bằng hash; Git head riêng không đại diện toàn bộ source bàn giao.

Trong thư mục đã giải nén, metadata paths tương đối vẫn đúng: data/raw, data/validated, data/metadata, data/prepared/<prepared_id>, artifacts/scalers/<scaler_id>. Không sửa file artifacts nếu có lỗi: kiểm tra gói/version hoặc yêu cầu bàn giao lại.

## 2. Tạo môi trường sạch

Chạy tại gốc đã giải nén:

```powershell
py -3.13 -m venv .venv/tv2_clean
.\.venv\tv2_clean\Scripts\python.exe -m pip install -r scripts/requirements-tv2-lock.txt
.\.venv\tv2_clean\Scripts\python.exe -m pip check
.\.venv\tv2_clean\Scripts\python.exe -X utf8 scripts/run_tv2_checks.py
.\.venv\tv2_clean\Scripts\python.exe -X utf8 scripts/verify_tv2_handoff.py
```

Không dùng --system-site-packages, không thêm eda_deps hoặc thư viện từ máy người gửi vào sys.path. Nếu máy dùng bản sklearn khác, loader sẽ từ chối; dùng lock đúng version. Pip tải package cần kết nối mạng lúc setup; dữ liệu/scaler/mẫu bàn giao được kiểm tra offline sau cài đặt. Không cần yfinance, notebook, PyTorch hoặc GPU để dùng gói preprocessing.

## 3. Đầu ra và consumer

Trong data/prepared/<prepared_id> có 6 NPZ và 12 JSON riêng cho 2 mode × 3 split; manifest ghi hashes, source identity và số mẫu/lý do loại. NPZ chứa X/y/target_indices, `allow_pickle=False`; inputs.json chứa raw Forecast Input, targets.json riêng chứa raw Target. X/y float64; việc tạo tensor float32 thuộc adapter training/model, phải kiểm tra riêng. Không đưa toàn bộ batch gồm y/targets vào inference.

```python
from pathlib import Path
import json
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.artifacts.prepared import load_prepared_modes
from backend.artifacts.scaler import load_scaler
from backend.data.preparation.contracts import build_inference_inputs

root = Path.cwd()
handoff = json.loads((root / "HANDOFF.json").read_text(encoding="utf-8"))
snapshot = load_tv1_snapshot(root, handoff["dataset_version"])
results, prepared_manifest = load_prepared_modes(
    root / "data/prepared" / handoff["prepared_id"],
    expected_dataset_version=handoff["dataset_version"],
    expected_source_hashes=snapshot["acceptance"]["hashes"],
    expected_scaler_id=handoff["scaler_id"],
)
scaler, _ = load_scaler(
    root / "artifacts/scalers" / handoff["scaler_id"],
    expected_dataset_version=handoff["dataset_version"],
    expected_source_hashes=snapshot["acceptance"]["hashes"],
)
batch = results[1]["splits"]["train"]  # results[5] cho direct 5 outputs
X, y = batch["X"], batch["y"]         # training/evaluation
input_only = build_inference_inputs(batch["inputs"], scaler)  # chỉ inputs/X
```

Chạy verify trước consumer: nó accept snapshot/scaler, load checksum-prepared, kiểm tra contract/leakage coverage, dựng lại bằng scaler cũ và so X/y/indices bằng nhau tuyệt đối; cấm fit/partial_fit và kiểm tra hash nguồn không đổi. Loader prepared đơn lẻ chỉ kiểm tra container/identity/checksum, không thay thế verify đối chiếu nguồn.

Snapshot đã chốt `aapl_2015_2025_acq_20261119T141302002415Z`: train scaler 2014 giá 2015–2022; mẫu 1 bước 1984/250/502, 5 bước 1980/246/498 (train/val/test). Mẫu IDs/ngày/input/target và exclusions theo docs/04. Không hard-code counts cho snapshot khác.

## 4. Dựng lại từ source tại workspace

```powershell
.\.venv\tv2_clean\Scripts\python.exe -X utf8 scripts/package_tv2_handoff.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z
```

Lệnh dùng scaler đã bàn giao, không fit mới. Tạo prepared ID/bundle/ZIP/checksum mới, không ghi đè. Nếu chủ động tạo scaler mới cho run mới, dùng build_tv2_scaler.py với version cụ thể rồi truyền thư mục scaler đó. Không refit trong đường verify/inference. Mọi artifacts sinh ra nằm ngoài Git theo .gitignore.

## 5. Bằng chứng và xác nhận máy khác

Runner lưu logs/audit/tv2_tests_<run>/ (log tests thật, summary, freeze, source hashes). Verifier lưu logs/audit/tv2_handoff_verify_<run>/summary.json. Run lỗi/nonzero không được nghiệm thu; không coi skip là pass. Giữ nguyên run cũ. Nếu lỗi giữa ghi prepared/scaler để lại thư mục dở, dùng ID mới, không nhận thư mục thiếu manifest.

Kiểm chứng local bằng venv sạch và thư mục giải nén mới chỉ chứng minh tái lập trên máy hiện tại. Thành viên nhận gói cần ghi tên người chạy, máy/OS/Python, SHA ZIP, IDs, hai logs, kết quả và lỗi nếu có; sau đó mới chốt xác nhận máy khác. Không tự đánh dấu recipient_machine_verified. Chưa upload Drive/push GitHub trong bước này.

Giới hạn nghiên cứu giữ nguyên: giá adjusted hồi cứu, lịch NASDAQ→XNYS tham chiếu; kiểm tra preprocessing không chứng nhận quá trình training không tuning trên test. Source code/report của model và kết quả thực nghiệm còn thuộc các TV sau.
