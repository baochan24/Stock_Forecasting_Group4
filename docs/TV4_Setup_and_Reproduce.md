# TV4 — setup, thực nghiệm và tái lập bộ bàn giao

Mục 10 đã kiểm thử source/artifacts trên bản sao độc lập cùng máy, strict 69/69 và reload 12 model đạt. Bộ bàn giao được tạo bằng scripts/build_tv4_handoff.py, kiểm sau giải nén bằng scripts/verify_tv4_handoff.py. Xem docs/TV4_Handoff_TV5_TV6.md và reports/audits/TV4_Item10_Handoff.md. Các receipt máy người nhận được ghi riêng khi có kết quả thực tế.

Sau sửa audit ngày 26/11/2026, chạy `.venv/tv4_clean/Scripts/python.exe scripts/verify_tv4_assets.py --root <thu_muc_project> --models` để kiểm inventory và nạp lại 12 model bằng đường dẫn tương đối. Manifest ở reports/audits/TV4_Run_Assets.json. Khi chuyển máy cần chuyển đủ các file được liệt kê, đặt cùng cấu trúc tương đối rồi tạo môi trường từ lock. Bản source backend đúng hash thời điểm train và hai entrypoint lịch sử nằm trong logs/audit/tv4_pre_fix_source_20261126. Không sửa nội dung metadata/checkpoint lịch sử để đổi ổ đĩa.

CLI training nhận `--plan-dir <thu_muc_cau_hinh>`, gồm one_step_lb10.yaml, one_step_lb30.yaml, one_step_lb60.yaml và five_step_lb30.yaml. Các output của run mới được đặt theo root workspace đang chạy.

Mục 9 dùng chung entrypoint training bằng `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/train_tv4_one_step.py --five-step`. Tùy chọn này đọc YAML năm bước đã khóa ở mục 7, chạy ba seed tại lookback 30, tạo run/checkpoint riêng dưới tv4_item9_<UTC> và kiểm loss tổng/từng horizon sau reload.

Mục 8 chạy bằng `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/train_tv4_one_step.py`. Mỗi lần gọi tạo đợt training mới, gồm chín run chính thức. Script đọc ba YAML lookback một bước đã kiểm chứng trong logs/audit/tv4_item7_20261125T120957429763Z, ghi YAML thực thi với output riêng, huấn luyện, reload từng best checkpoint rồi tổng hợp validation theo lookback. Xem notebook mục 8 để đọc lại kết quả đã lưu.

Mục 7 tái lập bằng `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/prepare_tv4_experiment_plan.py`. Script tạo bốn YAML chính thức và artifacts ID mới, audit đầy đủ từng lookback, kiểm chung ngày target, chạy probe một epoch mỗi cấu hình và reload. Bản đã kiểm chứng nằm tại `logs/audit/tv4_item7_20261125T120957429763Z/`. Dùng các YAML không có tiền tố probe_ cho run chính thức. Kế hoạch và ngân sách ở reports/audits/TV4_Item7_Experiment_Plan.md.

Chạy `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/check_tv4_smoke.py` để tái lập mục 6. Cả hai horizon chạy ba epoch toàn bộ train/validation, seed 42, CPU float64 và một luồng PyTorch. Summary ghi thời gian train, validation, median inference batch 32 qua 30 lượt sau 5 lượt làm nóng, số tham số và đối chiếu checkpoint. Tổng thời gian còn bao gồm kiểm dữ liệu và lưu/nạp.

Tái lập mục 5 bằng `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/check_tv4_training_run.py --checkpoint`. Phép thử huấn luyện 33 cửa sổ đầu mỗi tập cho LSTM một bước, lưu best theo validation, nạp instance mới rồi so toàn bộ dự báo validation với model best trong RAM bằng dung sai 0. Metadata checkpoint có cấu hình, seed, best epoch/loss và provenance TV2.

Từ gốc workspace, chạy `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/check_tv4_training_run.py` để tái lập mục 4 trên 33 cửa sổ train và 33 cửa sổ validation AAPL một bước. Phép thử dùng dữ liệu bàn giao TV2, seed 42, một luồng CPU và chọn best trong RAM. Đường dẫn JSON in ở cuối dẫn tới thư mục chứa CSV và metadata. Các ca cố ý gây lỗi hoặc ngắt run thuộc bộ `tests/training` trong lệnh `run_tv4_checks.py --require-clean`.

Windows64-bit, CPython3.13.7, torch CPU. Môi trường riêng `.venv/tv4_clean` không kế thừa system/user packages, dependencies69 pins trong `scripts/requirements-tv4-lock.txt`: TV3 pins cộng PyYAML6.0.3. Không thay lock/venv TV1–TV3. Đây là version lock Windows, chưa là wheel-hash/offline lock hoặc chứng nhận Linux/macOS.

```powershell
py -3.13 -m venv .venv/tv4_clean
.\.venv\tv4_clean\Scripts\python.exe -m pip install -r scripts/requirements-tv4-lock.txt
.\.venv\tv4_clean\Scripts\python.exe -X utf8 scripts/run_tv4_checks.py --require-clean
.\.venv\tv4_clean\Scripts\python.exe -X utf8 scripts/build_member_notebooks.py --member 4
.\.venv\tv4_clean\Scripts\python.exe -X utf8 scripts/execute_member_notebooks.py --member 4
```

Builder từ chối ghi đè notebook đã có; chỉ thêm --overwrite khi chủ động regenerate rồi execute lại. Chọn interpreter `.venv/tv4_clean/Scripts/python.exe` trong VS Code. Executor dùng kernel riêng aapl-coursework-tv4, không thay kernel TV2/TV3 khi chỉ chạy --member4. Notebook04_TV4_Training_and_Experiments.ipynb nằm trong notebooks/.

Runner lưu summary.json, pytest.log, junit.xml, pip-check.log, requirements-freeze.txt ở logs/audit/tv4_tests_<UTC>/. Strict mode kiểm nguồn imports đúng venv, pins, user/system site tắt, torch không CUDA, entrypoints workspace và không fail/error/skip. Nếu có receipt intake local, kiểm protected hashes TV1–TV3/data/scaler; máy clone không có receipt không được coi tự có chứng nhận intake này.

Unit tests của TV4 dùng dữ liệu tổng hợp. Mục 3 trong notebook cần bộ artifacts trong gói bàn giao TV2, đặt theo đúng cấu trúc của workspace. Hai YAML xác định phiên bản TV1 ở data/raw, data/metadata và data/validated, scaler ở artifacts/scalers và bộ cửa sổ ở data/prepared. Từ gốc project, chạy `.venv/tv4_clean/Scripts/python.exe -X utf8 scripts/check_tv4_aapl_data.py`. Có thể thêm `--config experiments/configs/lstm_one_step_baseline.yaml` để kiểm tra riêng một mô hình. Script chạy forward ở chế độ inference, ghi số mẫu, batch, khoảng ngày, hash danh sách ID theo thứ tự và nguồn artifacts vào logs/audit/tv4_item3_<UTC>/summary.json.

Receipt logs/audit/tv4_item1_20261125/intake.json ghi9 file/commit/hash và mapping runner. Xác nhận máy khác/official checkpoints chưa có. Trạng thái: reports/audits/TV4_Progress.md.
