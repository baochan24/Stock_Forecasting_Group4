# Môi trường và Dependencies

Phiên bản: 1.0 — 13/11/2026
Trạng thái: bản đặc tả trước triển khai. Phiên bản thư viện cần kiểm chứng thực tế khi cài đặt; cập nhật lại file này sau khi xác minh.

## 1. Python

| Thuộc tính | Giá trị |
|---|---|
| Phiên bản | Python 3.10.x hoặc 3.11.x (chọn một, cả nhóm dùng chung) |
| Quản lý môi trường | `venv` (built-in, không yêu cầu Anaconda) |
| Hệ điều hành hỗ trợ | Windows 10/11 (phát triển chính), macOS/Linux (cần kiểm tra) |

Tạo và kích hoạt môi trường:

```bash
# Tạo
python -m venv .venv

# Kích hoạt (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Kích hoạt (macOS/Linux)
source .venv/bin/activate
```

## 2. Dependencies chính

| Thư viện | Mục đích | Ghi chú |
|---|---|---|
| `torch` (CPU) | Xây dựng và huấn luyện LSTM, CNN | Cài bản CPU: `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| `numpy` | Tính toán số học | Dùng bởi hầu hết module |
| `pandas` | Đọc/xử lý dữ liệu dạng bảng | Acquisition, validation, preparation |
| `scikit-learn` | StandardScaler | Chỉ dùng `StandardScaler`, không dùng model ML khác |
| `yfinance` | Tải dữ liệu AAPL từ Yahoo Finance | Chỉ dùng ở acquisition, chạy một lần |
| `matplotlib` | Biểu đồ loss, dự báo, phân tích lỗi | Reports và notebooks |

## 3. Dependencies phát triển

| Thư viện | Mục đích |
|---|---|
| `pytest` | Chạy test |
| `ruff` | Lint và format code (thay thế `flake8` + `black`) |

## 4. Dependencies web (chưa chốt)

Framework API và front-end chưa được chọn (xem `10_Open_Decisions.md`). Khi chốt, bổ sung vào mục này và cập nhật `requirements.txt`.

Các ứng viên ghi nhận:
- API: `flask`, `fastapi` + `uvicorn`
- Front-end: Streamlit (đơn giản, phù hợp coursework) hoặc React/Vue (nếu nhóm có kinh nghiệm)

## 5. File requirements

Duy trì hai file ở gốc project:

### `requirements.txt` — dependencies chạy chính

```text
torch
numpy
pandas
scikit-learn
yfinance
matplotlib
```

### `requirements-dev.txt` — dependencies phát triển

```text
-r requirements.txt
pytest
ruff
```

Cài đặt:

```bash
# Production
pip install -r requirements.txt

# Development (bao gồm production)
pip install -r requirements-dev.txt
```

> **Quan trọng:** Sau khi cài thành công lần đầu, chạy `pip freeze > requirements-lock.txt` để ghi lại phiên bản chính xác. File lock này dùng để các thành viên khác cài đúng phiên bản. Không commit `.venv/` lên Git.

## 6. Kiểm tra môi trường

Sau khi cài xong, chạy kiểm tra nhanh:

```bash
python -c "import torch; print('PyTorch', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "import pandas; print('Pandas', pandas.__version__)"
python -c "import sklearn; print('scikit-learn', sklearn.__version__)"
```

Kết quả mong đợi: PyTorch in `CUDA available: False` (project dùng CPU). Ghi lại output vào metadata của run.

## 7. Quy tắc

- Cả nhóm dùng **cùng phiên bản Python** và **cùng phiên bản thư viện chính** (torch, numpy, pandas, sklearn).
- Không cài thêm thư viện mà không thông báo nhóm và cập nhật file này.
- `.venv/` nằm trong `.gitignore`, không commit.
- Khi bàn giao release, hướng dẫn nhận artifacts kèm lệnh cài dependencies.
- Seed không bảo đảm kết quả giống tuyệt đối giữa các máy/OS khác nhau — ghi nhận sự khác biệt nếu có.

## 8. Việc cần làm

- [ ] Chọn chính xác Python 3.10 hay 3.11
- [ ] Cài thử và ghi phiên bản lock
- [ ] Chọn framework web và bổ sung dependencies
- [ ] Kiểm tra trên máy ít nhất hai thành viên
