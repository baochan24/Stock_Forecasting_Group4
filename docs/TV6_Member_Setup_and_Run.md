# Hướng dẫn thành viên cài đặt và chạy AAPL Forecast Lab

Cập nhật 27/11/2026. Hướng dẫn chạy lại demo API/frontend từ model đã train; **không cần train lại, Docker hoặc GPU**. Các lệnh dưới dùng Windows PowerShell, chạy từ thư mục gốc project có `rule.md`, `backend/`, `frontend/` và `scripts/`.

Đã kiểm demo trên máy phát triển. **Cài mới và chạy trên máy thành viên khác chưa được nghiệm thu.** Tài liệu này không thay thế bước kiểm máy khác/bàn giao cuối ở mục10.

## 1. Cần cài gì?

| Thành phần | Dùng để làm gì? | Có bắt buộc không? |
|---|---|---|
| Windows64-bit và CPython3.13.7 64-bit | Môi trường đã dùng để kiểm project | Đây là cấu hình tham chiếu; hệ điều hành/Python khác chưa kiểm |
| Dependencies trong `scripts/requirements-tv6-api-lock.txt` | PyTorch, xử lý dữ liệu và API | Có; file này tự bao gồm TV4 core lock |
| Chrome hoặc Edge | Mở giao diện | Có trình duyệt hiện đại là đủ để xem demo |
| Git | Clone/cập nhật source | Cần nếu nhận source qua Git |
| Node22+ và Chrome cài sẵn | Test JavaScript và browser tự động | Chỉ cần khi chạy các test frontend; không cần để dùng demo |
| VS Code/Jupyter | Đọc/chạy notebook | Tùy chọn; không cần để mở website |
| Docker/CUDA/GPU | Không dùng trong luồng demo hiện tại | Không cần |

Không cần `npm install`, build frontend, tải lại Yahoo Finance hoặc sao chép `.venv` của leader. Mỗi máy tạo môi trường riêng. Cần Internet khi cài dependencies; demo đã nhận đủ source/artifacts sẽ đọc snapshot local.

## 2. Nhận đúng source và đủ artifacts trước

Repo: https://github.com/baochan24/Stock_Forecasting_Group4. Dùng đúng branch/commit hoặc bản source được leader bàn giao; không mặc định mọi thay đổi local đã được push lên Git. Không dùng checkout lồng `Stock_Forecasting_Group4/` trong workspace làm nguồn trạng thái.

**Chỉ clone Git chưa đủ để chạy demo:** dataset/scaler/checkpoint/sidecar sinh ra không đưa vào Git theo quy tắc project. Thành viên cần nhận thêm:

| Bộ cần nhận | Vị trí tương đối cần giữ |
|---|---|
| Manifest release | `artifacts/releases/aapl-research-residual-v1/manifest.json` |
| Registry release | `experiments/configs/tv6_research_release_v1.registry.json` |
| Snapshot validated | Đường dẫn `semantic.snapshot` trong manifest |
| 6 checkpoint LSTM residual và3 checkpoint CNN, các scaler và file đi kèm | Đúng các đường dẫn trong `semantic.files_sha256` của manifest |
| Stored results và history/metadata9 experiment của API | Toàn bộ `artifacts/releases/aapl-research-residual-v1-api-data/` |
| Registry sidecar API | `experiments/configs/tv6_api_data_v1.registry.json` |
| Source API, frontend, script chạy và locks | `backend/`, `frontend/`, các file `scripts/` của bản được leader bàn giao |

Manifest là danh sách chính xác file và SHA cần có. **Giữ nguyên cả cây đường dẫn tương đối**, kể cả checkpoint CNN nằm dưới `logs/audit/.../checkpoints/`; không gom tất cả `.pt` vào một thư mục. Source Python đã pin trong release cũng phải khớp hash, không chỉ weights.

ZIP `aapl-research-residual-v1.zip` của mục7 chỉ là gói **inference**. ZIP này chưa chứa API/frontend/sidecar mới và chưa phải gói web hoàn chỉnh. Nếu chỉ nhận ZIP đó, cần xin leader bổ sung các phần trên trước khi chạy web. Gói bàn giao đầy đủ/kênh tải cuối sẽ được chốt ở mục10; tài liệu này không tạo hoặc upload gói mới.

Không tự chạy training, sửa manifest/hash hoặc tải snapshot mới để thay file thiếu. Không yêu cầu máy thành viên dựng lại sidecar từ logs nghiên cứu: nhận sidecar đã nghiệm thu cùng registry tương ứng.

## 3. Tạo môi trường Python riêng

Mở PowerShell tại thư mục gốc project. Kiểm Python đang có:

```powershell
py -3.13 --version
py -3.13 -c "import sys, struct; print(sys.version); print(struct.calcsize('P') * 8)"
```

Cấu hình tham chiếu là3.13.7 và64-bit. Nếu máy không có launcher `py`, dùng đường dẫn đầy đủ tới Python3.13.7 thay cho `py -3.13` trong lệnh tạo môi trường.

Tạo môi trường mới (tên `tv6_demo` dùng cho máy thành viên, không thay môi trường của leader):

```powershell
py -3.13 -m venv .venv/tv6_demo
.venv/tv6_demo/Scripts/python.exe -m pip install -r scripts/requirements-tv6-api-lock.txt
.venv/tv6_demo/Scripts/python.exe -m pip check
```

Nếu `.venv/tv6_demo` đã tồn tại, kiểm đó có đúng môi trường của bạn trước; không ghi đè môi trường đang dùng cho công việc khác. File lock API đã tham chiếu `requirements-tv4-lock.txt`, nên phải giữ cả hai file trong `scripts/`.

Kỳ vọng `pip check` báo `No broken requirements found.` Không bỏ pin hoặc nâng/hạ package riêng lẻ để lệnh cài vượt qua lỗi; ghi lại lỗi/version rồi gửi leader kiểm tra. Nếu chỉ có source hoặc thiếu wheel phù hợp, dừng ở bước cài, chưa coi demo chạy được.

Các lệnh luôn gọi đầy đủ `python.exe` trong môi trường nên **không cần Activate.ps1** hoặc đổi PowerShell execution policy. VS Code không tự chọn kernel đúng thay cho các lệnh này.

## 4. Kiểm release và sidecar trước khi chạy web

```powershell
.venv/tv6_demo/Scripts/python.exe scripts/verify_tv6_release.py
```

Kỳ vọng JSON có `passed: true`, đúng release ID và các checks đạt. Script nạp model/scaler, chạy inference kiểm tra; không train hoặc fit lại.

Kiểm thêm sidecar API:

```powershell
.venv/tv6_demo/Scripts/python.exe -c "from pathlib import Path; from backend.artifacts.research_release import validate_release; from backend.services.results.release_results import ReleaseResults; root=Path.cwd(); release=validate_release(root); sidecar=ReleaseResults(root).validate(release); print({'passed': True, 'rows': sidecar['rows'], 'release_sha256': release['semantic_sha256']})"
```

Bộ hiện tại có20.144 dòng stored results, release ID `aapl-research-residual-v1` và semantic SHA:

```text
a4b04a50c3e499b95407a5a8f9de379a40f6371bbb532cc01df90fdb2b5719a3
```

Hash sai/thiếu file phải sửa bằng cách nhận đúng bản bàn giao; không tự cập nhật checksum. Verifier không chứng minh model dự báo tốt hơn baseline, chỉ kiểm bộ phát hành và inference.

## 5. Chạy API và frontend bằng hai terminal

**Terminal1 — API**, từ gốc project:

```powershell
.venv/tv6_demo/Scripts/python.exe scripts/run_tv6_api.py
```

Giữ terminal này mở. Kỳ vọng có `Uvicorn running on http://127.0.0.1:8000`. Swagger: http://127.0.0.1:8000/docs.

**Terminal2 — frontend**, cũng từ gốc project:

```powershell
.venv/tv6_demo/Scripts/python.exe scripts/run_tv6_frontend.py
```

Mở **http://127.0.0.1:5173**, chờ nhãn **API sẵn sàng**. Không mở `frontend/index.html` bằng `file://` hoặc Live Server: frontend cần proxy `/api/v1/` của script trên. Nếu API đã chạy đúng bộ, không khởi động bản thứ hai trên cùng port.

Website chỉ truy cập local trên máy đang chạy. Trên máy thành viên, `127.0.0.1` là chính máy thành viên, không phải máy leader; đây chưa phải triển khai dùng chung qua Internet/LAN.

Đổi port khi cần, đồng bộ port API trong hai lệnh:

```powershell
# Terminal1
.venv/tv6_demo/Scripts/python.exe scripts/run_tv6_api.py --port 8001

# Terminal2
.venv/tv6_demo/Scripts/python.exe scripts/run_tv6_frontend.py --port 5174 --api-port 8001
```

Khi đó mở http://127.0.0.1:5174. Dừng server bằng Ctrl+C trong từng terminal. Sau cập nhật source, dừng/chạy lại server rồi tải lại trang; API không bật auto-reload.

## 6. Kiểm nhanh trên máy thành viên

Terminal3, trong lúc hai server đang chạy:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/readiness
```

Health kỳ vọng `status=ok`; readiness kỳ vọng `status=ready`,9 models verified và results verified. Health200 riêng lẻ chưa chứng minh artifacts dùng được. Readiness lần đầu có nạp kiểm model nên cần chờ.

Trên giao diện:

1. Chọn ngày gốc `2025-06-16`,1 phiên,seed42,LSTM/CNN/persistence. Chạy dự báo: bảng có3 dòng target `2025-06-17`, có actual/error.
2. Chọn5 phiên: CNN bị bỏ/disable, kết quả cũ bị xóa. Chạy lại: có10 dòng LSTM/persistence, đủ T+1..T+5.
3. Màn So sánh: đọc metric toàn tập rồi khoảng ngày gốc; nhãn phạm vi khác nhau, không coi một ví dụ dự báo là metric toàn tập.
4. Xem history/audit của run và trace LSTM: trace verified,30 bước input. Nhật ký ghi request thành công trong tab; tải lại trang sẽ mất.

Lưu phiên bản Windows/Python, kết quả `pip check`, verifier, health/readiness, ngày/horizon/seed và ảnh chụp hoặc lỗi thực tế gửi leader để nghiệm thu máy khác. Chưa chạy thì không đánh dấu đạt.

Kiểm thử tự động là tùy chọn, chạy từ gốc project:

```powershell
.venv/tv6_demo/Scripts/python.exe -m pytest tests/api/test_tv6_api.py -q -p no:cacheprovider
node --test tests/frontend/test_ui_contract.mjs
```

`scripts/check_tv6_frontend.mjs` hiện dùng cố định `.venv/tv4_clean/Scripts/python.exe` và đường dẫn Chrome trên máy phát triển. **Không chạy nguyên script này trên môi trường `tv6_demo` rồi kỳ vọng nó tự chọn đúng Python.** Kiểm browser tự động portable sẽ được xử lý khi bàn giao cuối; các bước kiểm thủ công trên vẫn áp dụng cho máy thành viên.

## 7. Lỗi thường gặp

| Dấu hiệu | Kiểm tra và xử lý |
|---|---|
| `py`/Python không tìm thấy | Cài/kiểm CPython đúng bản, hoặc dùng đường dẫn đầy đủ tới interpreter |
| `ModuleNotFoundError` cho torch/fastapi/backend | Dùng đúng `.venv/tv6_demo/Scripts/python.exe`, cài lock; chạy script từ gốc project |
| NumPy lỗi `_multiarray_umath` | Kiểm `sys.executable`/`numpy.__file__`, đúng Python64-bit; không thêm `.venv/eda_deps` vào sys.path; gửi thông tin môi trường nếu vẫn lỗi |
| Thiếu manifest/checkpoint/snapshot/sidecar | Clone chưa đủ; nhận đúng artifacts và giữ nguyên đường dẫn tương đối |
| `checksum mismatch` hoặc readiness503 | Xem log API, chạy lại verifier/kiểm sidecar; nhận đúng source/artifacts, không sửa hash |
| Health200 nhưng readiness503 | Tiến trình sống nhưng bộ phát hành chưa sẵn sàng; không coi là đã chạy thành công |
| Port8000/5173 đã được dùng | Dùng server đúng bộ đang có hoặc chọn port khác theo mục5; không tắt process không rõ nguồn |
| UI báo backend chưa kết nối | Chờ API startup, kiểm port proxy khớp, bấm Kết nối lại; giữ cả hai terminal mở |
| 422 cho ngày hoặc horizon | Dùng ngày từ danh sách hợp lệ; h5 không CNN, không qua ranh target validation/test |
| UI vẫn hiện source cũ | Khởi động lại server, tải lại trang; không mở bản copy khác/file:// |
| Notebook lỗi dù web chạy được | Kernel notebook là lựa chọn riêng. Kiểm `sys.executable`, chọn interpreter môi trường đúng; không cần mở notebook để dùng web |

## 8. Phạm vi kết quả

Demo dùng snapshot adjusted close lịch sử2015–2025, không có giá live và không phải công cụ giao dịch. API/frontend không làm model chính xác hơn. Residual LSTM được phát triển sau khi xem test cũ; kết quả đó không phải holdout độc lập.

Tham khảo: [contract release](TV6_Release_Contract.md), [API](TV6_API_Setup_and_Contract.md), [kịch bản frontend](TV6_Frontend_Demo.md), [nghiệm thu mục9](../reports/audits/TV6_Item9_Frontend.md).
