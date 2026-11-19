# TV1 — hạng mục 10: tài liệu và tái lập

## Đã thực hiện

- Hướng dẫn chính: `docs/TV1_Setup_and_Reproduce.md`, gồm source mới nhất chưa mặc định có trên GitHub, Drive ZIP/hash, receipt, vị trí file, môi trường sạch, kernel, flow tests → notebook, lỗi thường gặp và checklist người nhận.
- Dependencies trực tiếp được ghim tại `notebooks/requirements-eda.txt`; full freeze sạch bàn giao tại `notebooks/requirements-tv1-lock.txt`, dùng cùng Windows/Python 3.13.
- `scripts/check_tv1_reproducibility.py` tạo bản source riêng, xác minh ZIP bàn giao và lấy data từ đó; không dựa vào dataset/venv phát triển có sẵn trong bản sao.
- Script execute hỗ trợ `TV1_NOTEBOOK_PYTHON` để chọn interpreter sạch; notebook không tự nạp binary từ eda_deps của môi trường khác.

## Kết quả kiểm chứng thực tế

Run `20261119T155705920238Z`, version `aapl_2015_2025_acq_20261119T141302002415Z`:

- Venv `.venv/tv1_clean`: Python 3.13.7, `include-system-site-packages = false`, user-site bị tắt.
- Workspace riêng `.venv/tv1_repro_20261119T155705920238Z`.
- ZIP/checksum/manifest hợp lệ, raw và validated cùng 2.766 dòng.
- `pip check` đạt; lưu `pip freeze` và log môi trường.
- **33/33 tests đạt**, 0 failure/error/skip.
- Toàn bộ code cell của notebook chạy xong, không lỗi; kiểm tra lại hashes data không đổi sau tests/notebook.
- Dependencies freeze được đối chiếu thêm bằng `pip install --dry-run --no-index -r notebooks/requirements-tv1-lock.txt` trên môi trường sạch đã chạy.

Logs và summary: `logs/audit/tv1_repro_20261119T155705920238Z/`; kết quả tests trong workspace riêng có đường dẫn trong summary. Pointer cục bộ: `data/metadata/tv1_reproducibility_latest.json`. Notebook mục 10 đọc bằng chứng này và hiển thị phạm vi cùng máy. Source/hash môi trường được lưu để truy vết.

## Giới hạn nghiệm thu

**Hoàn thành tài liệu và tái lập cục bộ trên môi trường sạch. Chưa hoàn tất xác nhận máy thành viên khác.** Không coi bản sao workspace cùng máy là người nhận độc lập hoặc bằng chứng hệ thống model/API/web chạy được. Người nhận cần phản hồi OS/Python, dataset version, ZIP hash, summary tests và notebook thực tế theo checklist hướng dẫn.

Calendar NASDAQ của thư viện là alias XNYS; giá hồi cứu không phải point-in-time; bối cảnh sự kiện không xác định nguyên nhân duy nhất. Chưa triển khai preprocessing TV2 hoặc training/model trong phần việc TV1. Không thay đổi dữ liệu, phạm vi hoặc tự merge/push GitHub.

## Bàn giao source và bằng chứng

Đã cập nhật mục 10 trực tiếp vào notebook chính và chạy lại bằng Python sạch: **19/19 code cell hoàn tất, không lỗi**; giao diện notebook có link mục 10 ở đầu file. Gói cục bộ `artifacts/releases/TV1_Source_Reproduce_20261119T155705920238Z.zip` gồm 69 file source/tests/docs/notebook/lock, receipt và log sạch, kèm manifest; không gồm .git, venv hoặc secrets. Dataset nhận từ ZIP riêng theo hướng dẫn.

SHA-256 gói source: `fca9e2aad45596306f15c5e1aa9f233821cfc8bfce5227fa28c1a3c0c04999de`. Sau khi người dùng xác nhận rõ quyền chia sẻ source TV1, đã [upload gói lên Drive Project_CW](https://drive.google.com/file/d/19fW252b7M430Rb5xVxCM6D8QtYT44UxU/view?usp=drivesdk), đọc lại metadata xác nhận thư mục cha. Gói là snapshot trước khi thêm link upload vào tài liệu cục bộ; source thực thi/kết quả không đổi.
