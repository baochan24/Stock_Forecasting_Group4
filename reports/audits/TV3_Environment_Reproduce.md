# TV3 mục5 — kiểm chứng môi trường CPU sạch và tái lập local

Ngày23/11/2026. **Đạt phần môi trường sạch/tái lập local; chưa xác nhận máy thành viên khác.** Mục6 bàn giao vẫn chờ. Không training AAPL, không checkpoint nghiên cứu hoặc metric dự báo.

## Đã thực hiện

1. Thu thập68 dependencies trực tiếp/gián tiếp theo Windows/Python3.13.7, lưu scripts/requirements-tv3-lock.txt. Lock SHA256 `b3c2b51dee9b06fc7399fbc81635530d38bcde77abbb1f68732f7520ec204648`.
2. Tạo `.venv/tv3_clean` mới, không --system-site-packages. Cài toàn bộ lock; không sửa TV1/tv2_clean hoặc venv audit cũ. Lock pin versions, không phải wheel-hash/offline lock.
3. Runner có --require-clean: xác minh prefix/user-site/pyvenv.cfg, origins của8 thư viện chính trong venv,68 versions khớp, torch.version.cuda=None, pip check, tests không lỗi/skip và source hashes không đổi. Giữ freeze --all (bao gồm pip bootstrap) và pip-check log.
4. Tạo bản source/artifacts độc lập dưới .venv/tv3_repro_<run>, chạy source từ thư mục đó bằng venv sạch, không PYTHONPATH tới project gốc. So hash mọi source/artifact trước/sau ở cả hai nơi.
5. Cập nhật và chạy notebook TV3 bằng kernel sạch. Đăng ký kernel người dùng `aapl-coursework-tv2-tv3`, display AAPL Coursework CPU float64, trỏ `.venv/tv3_clean/Scripts/python.exe`.

## Kết quả thực chạy

| Kiểm tra | Kết quả | Evidence |
|---|---|---|
| Tests workspace qua notebook | 89/89,0 fail/error/skip | logs/audit/tv3_tests_20261123T030530643561Z/summary.json |
| Isolation/versions/CPU/pip | clean=true, user_site=false,0 lock mismatches, CPU build=true, pip-check exit0 | Cùng test summary; module_origins, freeze, pip-check.log |
| Notebook TV3 | 21 cells/12 code,12/12 đạt | logs/audit/member_notebooks_20261123T030454864977Z/summary.json |
| Source copy độc lập: tests | 89/89, exit0, require-clean | logs/audit/tv3_repro_20261123T030500403955Z/tests_summary.json |
| Source copy: integration TV2 | 5460 samples, float64/shape/identity/scaler/artifact checks đạt | Cùng thư mục/integration_summary.json |
| Source copy: trace | Hai mode×3 stages đạt; reload trace exact, no side effects | Cùng thư mục/trace_summary.json |
| Source/artifact bất biến | Tất cả hash bản gốc/bản sao khớp | Cùng thư mục/summary.json và copied_hashes |

Thư mục bản sao `.venv/tv3_repro_20261123T030500403955Z` giữ source/logs đầy đủ; root logs/audit/tv3_repro_20261123T030500403955Z giữ bản copy summaries/stdout. Các bước tests/integration/trace ở bản sao đều exit0. Đây không phải performance benchmark; thời gian52.43/85.76/44.38 giây gồm startup/import/checks/logs và tải máy đồng thời.

## Cách chạy lại

Theo docs/TV3_Setup_and_Reproduce.md. Lệnh trọng tâm:

```powershell
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/run_tv3_checks.py --require-clean
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/check_tv3_reproducibility.py
.\.venv\tv3_clean\Scripts\python.exe -X utf8 scripts/execute_member_notebooks.py --member 3
```

Tests có fixture/file tạm, notebook kernel cần quyền filesystem/socket local phù hợp; những lượt trên được chạy với quyền phù hợp. Cài dependencies cần mạng/cache; dùng data/scaler/prepared cố định sau cài, không tải Yahoo. Không chạy training/tuning/test performance.

## Còn lại và giới hạn

Venv sạch và bản sao độc lập đều trên máy hiện tại. `recipient_machine_verified=false`; người nhận phải tự ghi người/máy/OS/Python/lock hash và logs khi nghiệm thu liên máy. Chưa certify Linux/macOS/Python khác; torch wheel/dependencies khác nền tảng cần lock CPU tương ứng. Trace schema vẫn nội bộ, chưa thành API TV6. Mục6 sẽ xử lý bàn giao và phối hợp checkpoint; chưa upload/push/merge trong mục5.
