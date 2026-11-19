# TV1 — cài đặt, nhận snapshot và tái lập

## Phạm vi và trạng thái

Chỉ AAPL adjusted close 2015–2025, CPU, dữ liệu → audit → bảng chuẩn → EDA → điều tra → tests. Không phải hướng dẫn chạy toàn hệ thống API/web/model. Dùng **source nhánh `Tâm`** cho phần TV1 đã audit; nhánh `main` chưa được tự merge. Các báo cáo theo run giữ nguyên trạng thái lịch sử trước lần commit này.

Version cố định: `aapl_2015_2025_acq_20261119T141302002415Z`. Bộ bàn giao giữ nguyên snapshot, không tải lại Yahoo để tái lập. Phạm vi ngày thực tế 2015-01-02–2025-12-31, 2.766 dòng.

## 1. Chuẩn bị source và môi trường sạch

Source cập nhật: [nhánh Tâm trên GitHub](https://github.com/baochan24/Stock_Forecasting_Group4/tree/T%C3%A2m). Gói source Drive cũ phía dưới là bản lịch sử trước hồi quy cuối; ưu tiên source nhánh này để có đủ 34 tests và sửa lỗi rollback validated/report. Dataset ZIP cố định vẫn dùng đúng bộ ở bước 2.

Dùng Windows x64 và Python **3.13.7** là môi trường đã kiểm chứng. Mở PowerShell ở gốc project (có backend/docs/scripts/notebooks). Nhận source TV1 mới nhất; giữ các thư mục tương đối. Không copy `.venv` từ máy khác.

Source TV1 đã được cho phép chia sẻ: [gói source và bằng chứng](https://drive.google.com/file/d/19fW252b7M430Rb5xVxCM6D8QtYT44UxU/view?usp=drivesdk), [checksum source](https://drive.google.com/file/d/1ReiEAf-25u4riV38c-28V0RH2SDaTumu/view?usp=drivesdk). SHA-256 `fca9e2aad45596306f15c5e1aa9f233821cfc8bfce5227fa28c1a3c0c04999de`. Gói không chứa dataset hoặc môi trường ảo; nhận dataset riêng theo bước 2. Dùng hướng dẫn TV1 này làm nguồn thao tác; một số README scaffold chung vẫn mô tả trạng thái ban đầu của toàn hệ thống.

```powershell
python --version
python -m venv .venv/eda
.venv/eda/Scripts/python.exe -m pip install -r notebooks/requirements-eda.txt
.venv/eda/Scripts/python.exe -m pip check
```

Tạo venv ở đường dẫn chưa tồn tại, **không dùng `--system-site-packages`** cho lần kiểm chứng sạch. Dependencies trực tiếp đã ghim: numpy 2.4.4, pandas 3.0.6, matplotlib 3.10.9, yfinance 1.8.0, exchange_calendars 4.13.3, nbformat 5.11.1, nbclient 0.11.0, ipykernel 7.4.0. Các dependency gián tiếp được lưu trong `requirements-freeze.txt` của lần kiểm chứng; chỉ dùng lại freeze từ cùng Python/OS. Cài thư viện cần mạng; kiểm tra snapshot/EDA/tests không cần tải Yahoo hoặc gọi Drive.

Bản freeze sạch đã được bàn giao thành `notebooks/requirements-tv1-lock.txt` (65 thư viện). Để khôi phục đúng cả dependencies gián tiếp trên Windows/Python 3.13, thay lệnh install ở trên bằng `.venv/eda/Scripts/python.exe -m pip install -r notebooks/requirements-tv1-lock.txt`. Bản lock được đối chiếu offline với môi trường đã chạy; không phải cam kết portable sang mọi OS/Python.

## 2. Nhận đúng artifacts

Thư mục: [Drive Project_CW](https://drive.google.com/drive/folders/16HyJmtmQ0YzfGHAGGtQ_qTSNEc6lQMwl).

- [ZIP đầy đủ](https://drive.google.com/file/d/1gfVBtM81snGI6x4rhqkAX6JZE9wavSfY/view?usp=drivesdk).
- [Checksum](https://drive.google.com/file/d/1j6nN6gRB_xzGvnxbt-fmmHqGSjr_iMM4/view?usp=drivesdk).
- ZIP: `aapl_2015_2025_acq_20261119T141302002415Z_complete_handoff_20261119T151339704353Z.zip`.
- SHA-256: `1aa67d814e5d68b3f275af88443dd31835974463dee1527cb747c049d7f7ea07`.

Lưu ZIP và `.zip.sha256` dưới `artifacts/releases/` đúng tên trên. Kiểm tra trước khi giải nén:

```powershell
python scripts/verify_tv1_handoff.py --archive artifacts/releases/aapl_2015_2025_acq_20261119T141302002415Z_complete_handoff_20261119T151339704353Z.zip --checksum artifacts/releases/aapl_2015_2025_acq_20261119T141302002415Z_complete_handoff_20261119T151339704353Z.zip.sha256
```

Kỳ vọng `passed: true`, raw_rows/validated_rows 2766. Giải nén vào thư mục tạm **mới**, chỉ chép cây `data/` sang source project mới để giữ code verifier mới nhất; giữ nguyên đường dẫn `data/raw`, `data/validated`, `data/metadata`. Không ghi đè file có hash khác. Nhận receipt `data/metadata/aapl_handoff_<version>_complete.json` từ gói source bàn giao cùng lần này; tests dùng receipt để tìm ZIP. Nếu thiếu receipt hoặc artifacts thì dừng và nhận đủ bộ, không đổi version để ép test đạt.

## 3. Chạy tests và notebook theo flow

```powershell
.venv/eda/Scripts/python.exe scripts/run_tv1_checks.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z
.venv/eda/Scripts/python.exe scripts/build_data_exploration.py
python scripts/execute_data_exploration.py
```

Suite hiện tại: **34/34**, không skip; kết quả thật được ghi vào `logs/audit/tv1_tests_<run_id>/`. Build tạo lại notebook và xóa output trước đó; execute chạy trên artifacts sẵn có, lưu output. Nếu chỉ muốn đọc, không cần build: mở notebook có output.

Notebook chạy thứ tự 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Gói validated đã xuất ở mục 2; audit mục 5/6 không ghi đè bộ cũ. Mục 9 đọc summary tests mới nhất đúng version, kiểm tra hash source/log/artifacts. Mục 10 đọc bằng chứng tái lập nếu có, không tự nhận máy khác đã chạy.

Muốn dùng Python khác đường dẫn mặc định, đặt biến `TV1_NOTEBOOK_PYTHON` thành đường dẫn tuyệt đối của Python venv đó trước lệnh execute. Không trộn `.venv/eda_deps` hoặc dependency của Python khác phiên bản vào sys.path/PYTHONPATH.

## 4. Chọn kernel trong VS Code

```powershell
.venv/eda/Scripts/python.exe -m ipykernel install --user --name aapl-eda-project --display-name "AAPL EDA (Python 3.13)"
```

Mở `notebooks/01_AAPL_Data_Exploration.ipynb`, chọn kernel AAPL EDA hoặc Python `.venv/eda/Scripts/python.exe`, Restart Kernel rồi Run All. Cell đầu in interpreter/version. Cấu hình workspace không thể đổi trực tiếp kernel cũ đang chạy; Reload Window nếu tab chưa đọc file cập nhật. Việc đăng ký kernel chỉ cần cho IDE; script execute tự tạo kernel cục bộ.

## 5. Thử tái lập tự động trong workspace riêng

Tạo một venv sạch khác rồi chạy:

```powershell
python -m venv .venv/tv1_clean
.venv/tv1_clean/Scripts/python.exe -m pip install -r notebooks/requirements-eda.txt
python scripts/check_tv1_reproducibility.py --python .venv/tv1_clean/Scripts/python.exe --dataset-version aapl_2015_2025_acq_20261119T141302002415Z
```

Script xác minh ZIP, tạo bản source riêng dưới `.venv/tv1_repro_<run_id>`, nhận các file data từ ZIP, kiểm tra venv không kế thừa user/system site, chạy pip check/freeze, tests và notebook. Logs/summary ở `logs/audit/tv1_repro_<run_id>/`; pointer `data/metadata/tv1_reproducibility_latest.json`. Không xóa/di chuyển bản gốc. Đây vẫn là **cùng máy**, không thay xác nhận thành viên khác.

## 6. Lỗi thường gặp và nghiệm thu

| Triệu chứng | Cách xử lý |
|---|---|
| NumPy `_multiarray_umath` | Dùng đúng Python 3.13 và venv đã cài dependencies, bỏ đường dẫn eda_deps cũ; restart kernel |
| Thiếu CSV/receipt/ZIP | Nhận đúng artifacts trên Drive và đặt đúng đường dẫn, không tải Yahoo thay thế |
| Sai hash | Dừng; tải lại đúng file/đối chiếu người bàn giao, không cập nhật hash để che lỗi |
| Tests source hash khác | Chạy lại runner sau thay đổi code rồi chạy notebook |
| FileExistsError khi download/validate | Giữ snapshot cũ, dùng version mới nếu thực sự muốn tạo dữ liệu khác |
| Drive 404/không truy cập | Kiểm tra tài khoản/quyền thư mục Project_CW; không giả upload thành công |

Người nhận gửi tên/ngày/OS/Python, dataset_version, ZIP hash, summary 34 tests và kết quả notebook để xác nhận độc lập. Hiện chưa có bằng chứng từ máy thành viên khác. Chỉ nghiệm thu phần tài liệu và kiểm chứng cục bộ theo kết quả thực tế; không tuyên bố toàn project/model/web hoàn thành.
