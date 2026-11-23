# TV3 — môi trường CPU và tái lập

Phạm vi mục5: source LSTM/trace/TV2 adapter và notebook, không training/checkpoint nghiên cứu. Chuẩn kiểm chứng Windows64-bit, CPython3.13.7. `scripts/requirements-tv3-lock.txt` ghi68 dependencies trực tiếp/gián tiếp đã chọn, gồm torch CPU, pytest, numpy/pandas/sklearn/calendar và notebook tools. Không dùng lock này như chứng nhận Linux/macOS; marker/dependency của torch khác nền tảng có thể cần wheel/lock CPU riêng.

## Cài môi trường mới

Tại gốc project có source và các artifacts TV1/TV2 cần thiết:

```powershell
py -3.13 -m venv .venv/tv3_clean
.\.venv\tv3_clean\Scripts\python.exe -m pip install -r scripts/requirements-tv3-lock.txt
.\.venv\tv3_clean\Scripts\python.exe -m pip check
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/run_tv3_checks.py --require-clean
```

Không thêm --system-site-packages hoặc chèn venv khác vào sys.path/PYTHONPATH. Không sửa môi trường TV1/TV2. Cài packages cần mạng/cache; tests và integration sau setup dùng snapshot/scaler/prepared cố định, không tải dữ liệu Yahoo. Lock ghi versions chứ chưa là wheel-hash lock hoặc bộ cài offline. Runner lưu pip-check/freeze (có pip bootstrap version), nguồn packages, source hashes/lock hash, Python/prefix/user-site và kết quả tests; strict-clean fail nếu không đúng môi trường/lock/CPU build hoặc có fail/error/skip.

Torch build trên Windows đã chọn phải có torch.version.cuda=None; tensors/model đều CPU float64. Điều này không tự áp dụng cho wheel cùng tên trên nền tảng khác. Nếu pip không tìm được đúng wheel/version cho Python/OS, không tự nới pin hoặc coi package hệ thống là thay thế.

## Kiểm dữ liệu thật và trace

Unit tests dùng fixtures tổng hợp và file tạm; chạy không cần snapshot thật. Integration/trace/notebook cần:

- TV1 version `aapl_2015_2025_acq_20261119T141302002415Z`: raw/metadata/validated/validation_report/quality_audit đúng đường dẫn.
- Scaler `artifacts/scalers/aapl_scaler_20261120T124720810874Z/` (2 JSON).
- Prepared `data/prepared/tv2_prepared_20261122T145943242978Z/` đủ manifest/NPZ/input-target JSON. Cách nhận và verify xem docs/TV2_Setup_and_Handoff.md; không chỉ clone source rồi giả định có artifacts.

```powershell
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/check_tv3_tv2.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z --prepared-dir data/prepared/tv2_prepared_20261122T145943242978Z
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/check_tv3_trace.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z --prepared-dir data/prepared/tv2_prepared_20261122T145943242978Z
```

Không fit/refit nguồn, không tính metric dự báo hoặc chọn model bằng test. Model weights khởi tạo/1 synthetic Adam step chỉ là probes kỹ thuật.

## Notebook

Chọn Python `.venv/tv3_clean/Scripts/python.exe` trong VS Code. Đọc outputs đã lưu không cần chạy lại. Khi chủ động cập nhật builder rồi regenerate (xóa outputs cũ), chỉ chọn TV3:

```powershell
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/build_member_notebooks.py --member 3 --overwrite
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/execute_member_notebooks.py --member 3
```

Mục5 notebook hiển thị nguồn packages/lock/freeze/pip-check cùng bằng chứng clean của chính phiên chạy. Mục6 vẫn chờ, chưa tự coi model đã bàn giao hoặc có checkpoint train. Tests có file tạm/kernel notebook cần quyền filesystem/socket local phù hợp; lỗi quyền môi trường phải ghi lại, không tính pass.

## Giới hạn nghiệm thu

Venv sạch trên cùng máy là kiểm chứng isolation, không là máy thành viên khác. Có thể tạo bản source/artifacts riêng để loại trừ phụ thuộc đường dẫn workspace, nhưng vẫn phải ghi rõ cùng máy. Người nhận chạy các lệnh và ghi OS/Python/lock hash/log IDs để chốt liên máy. Không bịa người nhận hoặc gửi kết quả thay họ. Không upload/push trong bước này, không thay ZIP TV2 đã chốt.
