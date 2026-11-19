# notebooks

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
