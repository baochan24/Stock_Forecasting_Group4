# Audit cuối TV1 — đối chiếu lại toàn bộ hạng mục

## Kết luận nghiệm thu

**TV1 đã đáp ứng phần việc dữ liệu cốt lõi tại workspace hiện tại, đủ điều kiện kỹ thuật chuyển bảng validated cho TV2. Chưa nghiệm thu đủ checklist bàn giao độc lập.** Có 8 hạng mục hoàn tất cục bộ; mục 2 và 10 đã cung cấp bộ file/hướng dẫn và tái lập cùng máy nhưng còn chờ một thành viên khác xác nhận nhận/chạy thành công. Không coi kết quả cùng máy là người nhận độc lập. Không yêu cầu TV1 làm scaler/windowing/model/API để lấp phần việc thành viên khác.

Audit run `20261119T161110977852Z`, dataset `aapl_2015_2025_acq_20261119T141302002415Z`. Đã đọc lại rule.md, docs/12_Team_Assignment.md và Data Flow Contract; kiểm tra lại code, artifacts và bằng chứng thực thi. Chưa merge/commit/push GitHub.

| # | Hạng mục | Kết luận | Bằng chứng |
|---|---|---|---|
| 1 | Thu thập | Đạt cục bộ | AAPL, Yahoo/yfinance, 2015–2025, raw cố định và hash |
| 2 | Bàn giao | Đủ bộ và đã upload; chờ người nhận | ZIP raw/validated/metadata/report, checksum, manifest; Drive readback đúng thư mục |
| 3 | Metadata/nguồn gốc | Đạt cục bộ | 16 kiểm tra khai báo/tính nhất quán; không tuyên bố xác thực độc lập Yahoo |
| 4 | Bảo vệ phiên bản | Đạt cục bộ | Chặn version có raw hoặc metadata trước gọi mạng; exclusive creation; tests trùng/race/error |
| 5 | Chất lượng | Đạt theo lịch tham chiếu | Ngày/giá/thiếu/trùng/thứ tự/OHLCV; đủ 2.766 phiên so NASDAQ alias XNYS |
| 6 | Bảng chuẩn | Đạt cục bộ | 14 kiểm tra schema/hash/ngày/giá; khớp raw–validated từng dòng |
| 7 | Khám phá | Đạt phạm vi mô tả | Thống kê năm, 5 hình, JSON/CSV có run ID; không tuning từ test |
| 8 | Điều tra bất thường | Đạt phạm vi 5 phiên gắn cờ | Close/Adj Close/cửa sổ phiên, ledger nguồn; giữ cả 5, không xác định nguyên nhân duy nhất |
| 9 | Kiểm thử | Đạt cục bộ sau sửa hồi quy | 34/34 test, không fail/error/skip, source và artifacts khớp hashes |
| 10 | Tài liệu/tái lập | Đạt hướng dẫn và venv sạch cùng máy; chờ máy khác | Dependencies trực tiếp + full lock, source/workspace riêng, pip check, 34 tests, notebook chạy hết |

## Phát hiện mới và xử lý trong lần audit

1. **Đã sửa lỗi ghi output khi validation report thất bại.** Trước sửa, lỗi ghi JSON có thể để CSV và report dở, khiến retry bị chặn. Đã tái hiện bằng fixture tổng hợp (`logs/audit/tv1_validation_write_probe.json`). Validator giờ reserve cả hai file bằng exclusive creation và dọn đúng file mới nếu bắt được lỗi. Test hồi quy mới xác nhận không còn bộ dở và retry thành công. Không sửa hoặc xuất lại dataset thật.
2. **Đã sửa tài liệu lỗi thời.** README gốc/raw/metadata còn ghi chưa có code/dataset; đã cập nhật. Báo cáo dữ liệu tách rõ thống kê của snapshot hiện tại với version PR cũ chưa có artifacts để kiểm chứng. Báo cáo implementation đã ghi module TV1 thực tế.
3. **Báo cáo validation trong ZIP là bản lịch sử.** Nó có liên kết hash đúng nhưng được tạo trước phần audit lịch/OHLCV mở rộng. Giữ nguyên ZIP/report cũ, dùng quality audit mới đi kèm; không giả rằng ZIP cũ đã chứa logic audit mới.

Tính bền khi process bị kill/mất điện vẫn có giới hạn: có thể còn file dở, lần sau bị từ chối để kiểm tra thủ công. Không tuyên bố two-file transaction chống mọi dạng sự cố filesystem.

## Kết quả dữ liệu được tính lại

| Nội dung | Kết quả |
|---|---:|
| Raw / validated | 2.766 / 2.766 dòng |
| Phạm vi phiên | 2015-01-02–2025-12-31 |
| Schema validated | date, ticker, adjusted_close, dataset_version |
| Số phiên 2015–2022 / 2023 / 2024–2025 | 2.014 / 250 / 502 |
| Return có thể tính | 2.765 |
| Giá adjusted min / median / max | 20,532551 / 88,164150 / 285,196411 USD |
| Giá adjusted mean / std | 105,955528 / 74,063170 USD |
| Return phân vị 1% / 99% | -4,8073% / +4,9447% |
| Ngày/giá thiếu, trùng, không hợp lệ, Inf, không dương | 0 |
| Phiên thiếu/thừa so lịch tham chiếu | 0 / 0 |
| Lỗi OHLCV | 0 |
| Dòng xóa / giá sửa | 0 / 0 |
| Phiên có absolute return >10% | 5, giữ nguyên |

Số phiên theo giai đoạn là mô tả, **chưa phải số mẫu windowing**, không fit scaler hoặc chia dữ liệu cho model ở TV1.

- Raw SHA-256: `cbcadbc002d05bc27a573114b9bb73b930733585b7823d147ca3477354479351`.
- Metadata: `71213959ec9c111a1826db9058dc41f61772af9a0324a4e32ff61eb3bf0edc24`.
- Validated: `ee56f9c782ac9e938985c680a9015d1ae198982e7d1cddc49ee5d67630c7b16d`.
- Cả raw/metadata/validated/validation report giữ nguyên hash qua tests và audit.

## Bằng chứng mới nhất

- Tests sau sửa: `logs/audit/tv1_tests_20261119T160931135922Z/`, 34/34 đạt.
- Tái lập sạch sau sửa: `logs/audit/tv1_repro_20261119T160957436492Z/`, 34 tests và notebook thành công; vẫn cùng máy. Code backend/data và tests/data hiện tại khớp bản đã chạy; tài liệu có thể được bổ sung sau kiểm chứng mà không đổi logic.
- Audit JSON: `data/metadata/tv1_final_audit_20261119T161110977852Z/summary.json`; quality tính lại nằm cùng thư mục. Pointer `data/metadata/tv1_final_audit_latest.json`.
- Drive metadata đọc lại trực tiếp ngày 19/11: gói dataset, checksum và source trước audit nằm đúng Project_CW. Chỉ là readback metadata, chưa tải lại bytes hoặc xác minh người nhận; code fix mới cần dùng source hiện tại/gói audit mới, không mặc định bundle cũ đã có fix.
- Notebook có phần **TỔNG AUDIT TV1 VÀ KẾT QUẢ DATA** ngay đầu sau cấu hình: bảng 10 hạng mục, kết luận có điều kiện, thống kê, 5 dòng đầu/cuối và hashes.

## Điều kiện còn mở

Người nhận cần dùng source cập nhật, đúng ZIP/checksum/receipt và dependencies, gửi summary tests/notebook từ máy của họ để chốt mục 2/10. Không tự tạo xác nhận. Lịch NASDAQ của thư viện ánh xạ XNYS; giá Yahoo điều chỉnh hồi cứu không phải point-in-time; nguồn sự kiện hỗ trợ bối cảnh chứ không xác định nhân quả. Các giới hạn này phải giữ trong báo cáo, không là lý do tự sửa giá hoặc mở rộng model ngoài phạm vi.

## Kết quả notebook và gói cục bộ

Notebook workspace đã chạy đủ **20/20 code cell, không lỗi** sau audit và sửa hồi quy. Phần tổng audit nằm ngay sau cell cấu hình, trước mục 1; không cần đọc file trên Drive để thấy kết quả.

Gói source/audit mới tại `artifacts/releases/TV1_Final_Audit_20261119T161110977852Z.zip`: 90 file, manifest và checksum `d7a883ea78a30f3b96fc803aed753442c24ec8f2628db670fc6950b468704c4e`. Không chứa dataset CSV, .git, venv hoặc secrets; dataset nhận riêng qua ZIP cố định. Gói là snapshot trước phần ghi chú trạng thái upload này, code và kết quả audit không đổi.

Upload gói mới bị automatic approval review từ chối vì quyền cho gói source có tên trước không bao phủ gói mới này. Đã xin xác nhận riêng cho đúng tên/nội dung và thư mục Project_CW; chưa upload khi chưa được xác nhận. Kết quả kiểm tra và notebook cục bộ đã hoàn tất độc lập với upload.
