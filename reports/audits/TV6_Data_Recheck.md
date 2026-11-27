# TV6 — kiểm lại bộ dữ liệu bàn giao

Theo yêu cầu kiểm lại dữ liệu sau nghiệm thu mục1. Chỉ đọc artifacts đã đóng băng và ZIP đã bàn giao, không tải lại nguồn, sửa/loại/điền phiên, fit scaler hoặc chạy model trên test.

## Nội dung kiểm

- Đối chiếu120 hashes trong danh mục intake, acceptance/quality/calendar/schema/provenance của snapshot TV1, adjusted_close raw hữu hạn và dương.
- Scaler version/hash/feature/currency/fit_split, recompute mean/variance/scale/count từ toàn bộ2014 dòng train2015–2022 bằng audit độc lập, không fit lại.
- Cả hai prepared bundles đang được9 checkpoints tham chiếu, đầy đủ mode1/5 và train/val/test. Kiểm manifest và checksum từng member, NPZ allow_pickle=False, float64/finite.
- Audit toàn bộ eligible target indices và số loại do thiếu history, target không đầy đủ hoặc vượt split; input trước target, tất cả5 target cùng split, ID/ngày/thứ tự/coverage đầy đủ.
- Inverse toàn bộ X/y về raw input/target JSON với rtol/atol1e-12, không chỉ một vài batch.
- So từng byte của data/scaler với ZIP có SHA256 đã nghiệm thu, kiểm provenance9 checkpoint, đối chiếu lại hash trước/sau để đảm bảo không sửa dữ liệu.

## Cách đọc số mẫu

Prepared gốc lookback30 có windows theo30 phiên lịch sử. Consumer một bước common-history60 lọc thêm các target đầu train để cùng population so sánh LSTM10/30/60; CNN vẫn input30. LSTM năm bước giữ config đã train, không đổi sang common-history60. Vì vậy số train prepared gốc khác train consumer là có chủ đích. Không bỏ mẫu validation/test do thiếu lịch sử ở đầu split, lịch sử tập trước vẫn dùng khi hợp lệ.

Ví dụ đầu/cuối mỗi split được lưu boundary_examples.json, bảng coverage.csv có raw_window_samples và samples_if_common_history60 riêng. Số test windows và target values chỉ dùng kiểm schema/coverage/inverse, không tính performance hoặc dùng để tuning.

Script tái lập scripts/recheck_tv6_data.py. Kết quả thật và notebook được cập nhật sau chạy. Giới hạn là consistency của snapshot local và gói bàn giao, không xác minh độc lập tính chính xác Yahoo hoặc point-in-time. Các giới hạn hồi cứu adjusted close của dữ liệu gốc giữ nguyên.

## Kết quả thực tế

Đạt kiểm dữ liệu bàn giao local. Snapshot2.766 dòng,120 hashes intake khớp,9 checkpoint cùng provenance đúng,2 prepared bundles đều audit thành công cả mode1/5 và3 splits. Inverse toàn bộ X/y khớp raw records, toàn bộ target coverage và loại windows tại ranh giới đúng.45 files data/scaler trong ZIP có bytes/hash khớp bản đang dùng. Không đổi file, không train hoặc tính performance test.

Receipt logs/audit/tv6_data_recheck_20261126T162229495967Z/summary.json, coverage.csv và boundary_examples.json cùng thư mục. Notebook06 bổ sung bảng kết quả/scaler/coverage, giữ output cũ. Không phát hiện sai lệch dữ liệu cần sửa trong phạm vi kiểm này. Mục2 TV6 vẫn chưa triển khai.
