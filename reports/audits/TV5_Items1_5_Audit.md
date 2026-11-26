# Audit TV5 mục 1–5

Ngày 26/11/2026. Đối chiếu rule.md, đề Topic 4 và thiết kế/decision log đã đọc trong phiên, source workspace và bằng chứng local. Không tiếp tục mục 6, không train AAPL hoặc đánh giá hiệu năng test trong audit này.

## Phát hiện cần theo dõi

1. Mức vừa, cần giải quyết trước mục 8. `comparison_reference` kiểm config hợp lệ, chưa là khóa thực nghiệm phương án A. Probe thay max_epochs thành 101 hoặc conv1_channels thành 32 vẫn được chấp nhận. YAML hiện tại đúng max100 và Conv1=16, chưa có run sai ngân sách. Cần fingerprint/kiểm config đã chốt trước official runs, checkpoint mục 6 phải lưu đủ cấu hình. Đây chưa phải lỗi đường train hoặc bằng chứng đã vượt ngân sách.
2. Mức vừa về tái lập, cần giải quyết khi bàn giao mục 10. `check_tv5_aapl_data.py` dùng YAML và metadata lịch sử TV4 trong logs. Các bằng chứng đó không nằm trong source Git theo rule. Git clone đơn thuần chưa đủ chạy notebook, phải có artifacts và log đối chiếu đúng version. Hiện chưa chứng nhận trên máy thành viên khác.
3. Mức thấp về tài liệu. Dòng cuối README CNN còn nói Adam/dropout/state_dict và dữ liệu AAPL sẽ kiểm ở bước sau, trong khi các mục 3/4 đã kiểm. Cần đồng bộ mô tả trạng thái, không thay kết quả lịch sử trong các báo cáo cũ.

Cập nhật khi hoàn thành mục 6, câu README cũ ở phát hiện 3 đã được đồng bộ. Hai việc khóa run phương án A và đóng gói log/artifacts vẫn được theo dõi trước mục 8/10.

Cập nhật mục 8, official entry point đã có lock/fingerprint phương án A và bảy tests chống drift, đã giải quyết yêu cầu khóa trước official runs ở phát hiện 1. Validator chung vẫn cho phép diagnostic, đường official kiểm lock riêng. Bàn giao artifacts/logs còn thuộc mục 10.

## Đối chiếu từng hạng mục

| Mục | Bằng chứng và phạm vi | Kết luận phạm vi |
|---|---|---|
| 1 | Intake ghi commit và ba source hashes; baseline bảy tests float32 bất biến; exports hiện tại khớp nguồn | Đủ bằng chứng tiếp nhận local |
| 2 | CPU float64 tường minh, không cast/global dtype; model 17.057 tham số; config/input/output guards và 26 tests | Đạt contract, chưa là khóa run chính thức |
| 3 | Cấu hình CNN bằng data reference LSTM; snapshot/scaler/prepared hashes và từng ID/ngày/X/y; forward toàn train/validation | Đạt dữ liệu/forward local |
| 4 | Backward/Adam hữu hạn batch1/32, dropout train/eval, file state_dict strict reload output bằng chính xác | Đạt diagnostic tổng hợp; chưa là checkpoint có provenance |
| 5 | Dùng trainer TV4 nguyên vẹn; factory/config CNN; chín tests tích hợp weighted loss/no_grad/tail/early stop/RAM runner | Đạt tích hợp tổng hợp; checkpoint persistence chờ mục6 |

Phép kiểm early stopping có plateau validation điều khiển để xác nhận logic, không dùng làm kết quả dự báo AAPL. Tổng 111 tests gồm hồi quy training TV4, không phải 111 tests riêng CNN.

## Giới hạn kết luận

Không có cơ sở kết luận CNN tốt hơn LSTM, không overfit hoặc hoàn toàn không leakage chỉ từ tests. Trong đường dữ liệu đã kiểm, dùng lại scaler fit train và split theo target; không tạo preprocessing hoặc training loop thứ hai. Loader kiểm schema/coverage dữ liệu test không đồng nghĩa tính metric trên test. Các mục 6–10 vẫn chưa nghiệm thu.

Audit thực thi bởi scripts/audit_tv5_items_1_5.py, lưu hashes source trước/sau, pytest/JUnit, data receipt và probes config vào logs/audit/tv5_audit_1_5_*. Kết quả thực thi được bổ sung sau khi hoàn tất.

Lượt audit mới đạt 111/111 tests, không lỗi/skip. Source backend/tests/config không đổi trong quá trình audit. Đối chiếu intake TV5 có đúng một thay đổi module được đăng ký, experiment_runner.py tại mục 5. Trainer, data factory, preprocessing và notebooks TV1–TV4 giữ hash đã bảo vệ.

Receipt audit ở `logs/audit/tv5_audit_1_5_20261126T040833735453Z/summary.json`. Forward AAPL đã chạy lại thành công trên toàn bộ 1.954 train/250 validation, không train. Kết luận có thể tiếp tục thiết kế checkpoint mục 6 theo flow; chưa chốt readiness cho official training mục 8 hoặc bàn giao mục 10.
