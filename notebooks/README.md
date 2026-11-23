# notebooks

**Sau TV3 mục6:** notebook03 hiện22 cells/13 code,13/13 chạy đạt bằng kernel sạch. Có toàn bộ6 mục,99 testcase, trace/precision/environment và checksum/receipt gói source/contract cuối. Đạt kỹ thuật local, vẫn chờ người nhận/máy khác/checkpoint AAPL thật. Reports/audits/TV3_Final_Handoff.md ghi kết quả; các counts/mục chờ bên dưới giữ lịch sử trước cập nhật.

**Kernel hiện tại sau TV3 mục5:** chọn **AAPL Coursework CPU float64**, interpreter `.venv/tv3_clean/Scripts/python.exe`. Đã chạy notebook03 bằng venv sạch theo lock68 packages;21 cells/12 code,12/12 đạt. Mục5 hiển thị origins/lock/pip-check/freeze và assertions strict-clean; mục6 chờ, máy khác chưa xác nhận. Các hướng dẫn tv3_review_env và counts cũ phía dưới giữ lịch sử, không phải môi trường mặc định hiện tại. Xem docs/TV3_Setup_and_Reproduce.md.

## Notebook theo từng phần để trình bày với giảng viên

Cập nhật TV3 mục4: notebook03 có thêm trace initial/update/reload của cả hai mode, bảng sai số,30 dòng gate/hidden/cell và biểu đồ, kiểm recurrence30×32. Mục5–6 chờ. Suite hiện89 tests; các ghi nhận mục1–3/77 tests phía dưới là lịch sử trước cập nhật.

Theo yêu cầu người dùng23/11/2026, mỗi phần TV dùng một notebook, các hạng mục là các nhóm Markdown/code cells. Cập nhật notebook sau từng mục, có output thật và đường dẫn evidence; không tạo kết quả trước khi chạy.

| Phần | Notebook | Nội dung hiện có |
|---|---|---|
| TV1 | `01_AAPL_Data_Exploration.ipynb` | EDA, nguồn dữ liệu và audit TV1 hiện có; giữ nguyên trong lần bổ sung này |
| TV2 | `02_TV2_Preprocessing_and_Audit.ipynb` | 10 mục: dữ liệu/split/scaler/window1/5/contract/tests/leakage/handoff; chờ xác nhận máy khác |
| TV3 | `03_TV3_LSTM_Development_and_Tests.ipynb` | Mục1–6 kỹ thuật local,99 tests/trace/clean-env/handoff receipt; chờ người nhận/máy khác/checkpoint thật |

TV4–TV6 sẽ bổ sung notebook khi bắt đầu phần tương ứng, không tạo notebook rỗng hoặc giả định đã hoàn thành. Notebook là bản trình bày gọi backend/scripts, không chứa pipeline thứ hai hoặc thay thế source/tests/report.

Hai notebook đã chạy và lưu outputs local: TV2 có25 cells/13 code; TV3 sau mục4 có19 cells/11 code. Không có error outputs. Có bảng dữ liệu/raw→scaled→inverse, biểu đồ split và mẫu input/target; TV3 hiển thị kiến trúc/dtype, kết nối dữ liệu thật, từng test và trace/biểu đồ gates. Mô hình minh họa chưa train; không có accuracy/MAE/RMSE dự báo.

Mở file trực tiếp trong VS Code để đọc output đã lưu, không cần Run All chỉ để xem. Khi chạy lại, chọn interpreter `.venv/tv3_review_env/Scripts/python.exe` (kernel AAPL Coursework TV2-TV3). Đây là môi trường phát triển kế thừa site packages, không phải chứng nhận môi trường sạch TV3 mục5. Cần artifacts TV1/TV2 tại workspace; không truy cập Yahoo để tải lại.

Build/execute đặt đúng trong scripts:

```powershell
# Chỉ regenerate TV3 khi chủ động cập nhật builder; việc này xóa output cũ.
.\.venv\tv3_review_env\Scripts\python.exe -X utf8 scripts/build_member_notebooks.py --member 3 --overwrite
.\.venv\tv3_review_env\Scripts\python.exe -X utf8 scripts/execute_member_notebooks.py --member 3
```

`--member 2` cho TV2; mặc định all cho cả hai. Builder từ chối ghi đè nếu thiếu --overwrite; executor giữ output và lỗi nếu thực thi thất bại để kiểm tra. Không regenerate để chỉ xem notebook. Sau khi cập nhật trên đĩa, mở lại tab để tránh xem bản buffer cũ. Runtime cần nbformat5.11.1, nbclient0.11.0, ipykernel7.4.0 và matplotlib cùng dependencies backend; đã cài tại venv riêng, không sửa TV1/tv2_clean. Chưa đóng lock sạch TV3, xem mục5 khi triển khai.

Run All thực sự chạy lại tests/audit, có thể mất vài phút và tạo log ID mới. Benchmark CPU trong TV3 đọc evidence đã ghi, ghi rõ đây là phép đo quá khứ/tổng hợp; không chạy training benchmark mỗi lần. ZIP bàn giao TV2 đã chốt trước các notebook này, không tự sửa hoặc tuyên bố ZIP chứa bản mới.

## Kết quả audit TV1 hiện hành

Ngay đầu `01_AAPL_Data_Exploration.ipynb`, sau cell cấu hình, có **TỔNG AUDIT TV1 VÀ KẾT QUẢ DATA**: bảng đủ 10 hạng mục, kết luận 8 đạt cục bộ/2 còn xác nhận độc lập, thống kê snapshot, schema, số phiên theo giai đoạn, 5 dòng đầu/cuối và hash. Audit đã sửa lỗi rollback output khi report ghi thất bại; suite hiện tại 34/34 và notebook 20/20 cell đạt. Xem `reports/audits/TV1_Final_Audit.md`; các thống kê theo run phía dưới giữ lịch sử.

Notebook khảo sát/demo sau này; gọi logic back-end, không nhân bản pipeline.

## Khám phá AAPL

Quy trình cập nhật: sau khi hoàn thành từng hạng mục TV1, bổ sung vào `01_AAPL_Data_Exploration.ipynb` mô tả công việc, kết quả thực thi, file bằng chứng, trạng thái và phần còn lại; đồng bộ `scripts/build_data_exploration.py` rồi chạy notebook để lưu output. Không đánh dấu hoàn tất chỉ dựa trên code hoặc số liệu chưa kiểm chứng.

Hạng mục 2 hiện đọc receipt `_complete.json`, kiểm tra bộ đủ raw/validated/metadata/report và hiển thị link ZIP/sha256 trên Drive. Phần cung cấp bộ artifacts đã hoàn thành, xác nhận người nhận độc lập vẫn chờ. Hạng mục 5 audit chất lượng mở rộng tiếp tục riêng.

Hạng mục 5 đã chạy trên snapshot hiện tại: validator dùng chung kiểm tra lịch phiên và chất lượng, lưu audit JSON riêng không ghi đè bộ đã bàn giao. Notebook hiển thị lỗi/cảnh báo và bảng phiên từng năm. Tests dữ liệu đạt 20/20 khi đặt `TV1_DATASET_VERSION` bằng version hiện tại. Năm biến động >10% được giữ cho điều tra hạng mục 8.

Hạng mục 6 tiếp nối mục 5 trong notebook: 14 kiểm tra chấp nhận bảng chuẩn, dựa vào hash nguồn/audit/report và đối chiếu raw–validated từng dòng. 24/24 tests dữ liệu đạt sau bổ sung test output. Bảng 2.766 dòng bốn cột không bị ghi đè; xem `reports/audits/TV1_Standard_Output.md`. Chưa chuyển sang preprocessing TV2.

Hạng mục 7 có các mục 7.1–7.7: giải nghĩa cột, độ phủ, diễn biến giá/volume, return/rolling volatility, phân bố năm và nhận xét tính từ dữ liệu. Xuất 5 PNG vào `reports/figures/`, bảng/summary vào `data/metadata/eda/<dataset_version>/<eda_run_id>/`, không ghi đè bằng chứng EDA run trước. Xem `reports/audits/TV1_Data_Exploration.md`. Không tuning hoặc giải thích nguyên nhân các biến động lớn ở bước này.

Hạng mục 8 cập nhật trực tiếp trong notebook (8.1–8.3, link đầu notebook): đối chiếu tất cả 5 phiên |return| >10%, Close/Adj Close và cửa sổ ±2 phiên; ledger nguồn cục bộ `reports/audits/TV1_Anomaly_Sources.json`. Giữ cả 5 phiên, không sửa snapshot. CSV/JSON review xuất trong `<eda_run_id>/anomaly_review/`, hình 5 panel ở `reports/figures/`. Xem `reports/audits/TV1_Anomaly_Review.md`; bối cảnh không phải kết luận nhân quả.

Hạng mục 9 hiển thị 34/34 test đạt, không skip, kết quả từng module và log đầy đủ. Chạy `scripts/run_tv1_checks.py --dataset-version <version>` trước; notebook chỉ đọc summary mới nhất đúng version và xác minh hash log/source/artifacts. Nếu sửa code test/backend cần chạy lại suite rồi Run All. Bằng chứng `reports/audits/TV1_Test_Summary.md`; chưa thay thế xác minh máy khác.

Hạng mục 10 có hướng dẫn `docs/TV1_Setup_and_Reproduce.md`, full lock `requirements-tv1-lock.txt` và kết quả clean venv/workspace riêng cùng máy: pip check đạt, 34 tests đạt, toàn bộ 20 code cell chạy thành công. Notebook hiển thị summary thực từ `data/metadata/tv1_reproducibility_latest.json`, không tự nhận máy khác đã chạy. Xem `reports/audits/TV1_Reproducibility.md`.

Mở `01_AAPL_Data_Exploration.ipynb` để xem bảng dữ liệu, đồ thị giá/khối lượng/biến động, audit lịch phiên và các hạng mục TV1 cần bổ sung. Mục 1 ghi đầy đủ bước thu thập bằng downloader TV1, version `aapl_2015_2025_acq_20261119T141302002415Z`: tham số tải, nguồn, metadata/hash, đối chiếu đầu ra và 10 dòng đầu/cuối. Đây là snapshot mới tải trong phiên làm việc, không phải artifacts gốc tác giả PR đã báo cáo.

Cài dependencies: `python -m pip install -r notebooks/requirements-eda.txt`. Chọn kernel Python đã cài các thư viện này rồi Run All. Notebook chỉ đọc snapshot đã lưu theo `DATASET_VERSION`; thiếu artifacts sẽ báo lỗi, không tự tải. Lệnh gọi downloader hiển thị trong Markdown để tham khảo, không chạy khi Run All. Bảng audit bổ sung xuất vào `data/metadata/eda/<dataset_version>/`, tách biệt output snapshot EDA cũ.

`../scripts/build_data_exploration.py` tạo lại notebook (xóa output cũ); `../scripts/execute_data_exploration.py` dùng môi trường `.venv/eda` để chạy/lưu output. Tạo môi trường sạch ở đường dẫn chưa có bằng `python -m venv .venv/eda`, cài bằng `.venv/eda/Scripts/python.exe -m pip install -r notebooks/requirements-eda.txt`. Build bằng `.venv/eda/Scripts/python.exe scripts/build_data_exploration.py`; execute bằng `python scripts/execute_data_exploration.py`. Có thể chỉ định Python khác bằng biến `TV1_NOTEBOOK_PYTHON` (đường dẫn tuyệt đối). Không copy venv giữa máy; xem `docs/TV1_Setup_and_Reproduce.md`.

Trong VS Code, chọn **Select Kernel → Python Environments → `.venv/eda/Scripts/python.exe`**, sau đó Restart Kernel và Run All. Cell đầu in đường dẫn Python để kiểm tra. Không thêm `.venv/eda_deps` vào sys.path: NumPy ở đó là binary CPython 3.13, không dùng được với kernel Python khác phiên bản. Nếu đã chạy cell cũ, cần restart để bỏ các module đã nạp dở.

Kernel đã đăng ký với tên `aapl-eda-project`, hiển thị `AAPL EDA (Python 3.13)`; notebook và các script build/execute cùng dùng tên này. `.vscode/settings.json` đặt interpreter mặc định cho workspace. Nếu tab đang giữ kernel cũ, dùng **Developer: Reload Window** để IDE đọc lại cấu hình và notebook; metadata trên đĩa không thể thay trực tiếp tiến trình kernel đang chạy. Khi chuyển sang máy khác, đăng ký kernel bằng `.venv/eda/Scripts/python.exe -m ipykernel install --user --name aapl-eda-project --display-name "AAPL EDA (Python 3.13)"`.

Raw CSV và các bảng audit xuất ra nằm dưới `data/`, được Git bỏ qua theo chính sách hiện tại. Không commit dataset qua notebook; bảng mẫu và biểu đồ được lưu trong output notebook để đọc trực tiếp. Không train, fit scaler hay chọn model tại đây.
