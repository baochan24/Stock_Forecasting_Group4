# Sơ khảo ngân sách TV5 trước quyết định kiến trúc

Cập nhật mục 2 ngày 26/11/2026, kiến trúc A giữ nguyên và dùng CPU float64 theo Decision Log. Ngân sách ba run/trần 300 epoch giữ nguyên. Các đoạn chờ quyết định phía dưới thuộc lịch sử trước mục 2.

**Cập nhật quyết định ngày 26/11/2026.** Người dùng đã chọn phương án A, giữ một cấu hình CNN tác giả, seeds 42/123/456, tối đa 100 epoch/run và patience 10. Tổng ba run, trần 300 epoch. Dtype CNN chờ quyết định riêng ở mục 2. Những phần ghi chưa phê duyệt bên dưới là lịch sử sơ khảo trước quyết định.

Ngày 26/11/2026. Trạng thái tham khảo, chưa phê duyệt kiến trúc/dtype hoặc ngân sách CNN, chưa thay source CNN và chưa chạy training.

## Ngân sách hiện có trong project

Thiết kế dùng CPU, yêu cầu đo thời gian và công bố ngân sách thử. Tài liệu chưa đặt trần tiền, RAM, tổng thời gian hay deadline cụ thể. docs/10_Open_Decisions.md vẫn để CNN và ngân sách tuning TV5 là phần mở. Giới hạn TV4 đã chốt là 12 run, ba seed, tối đa 100 epoch/run, patience 10 và tổng 1.200 epoch.

Kết quả thực tế TV4 gồm 12 run, 1.075 epoch. Một bước dùng 775 epoch và 1.266,994 giây trong trainer, năm bước dùng 300 epoch và 355,733 giây. Tổng khoảng 27,05 phút trong trainer, chưa gồm toàn bộ chuẩn bị dữ liệu, smoke, tests và kiểm chứng.

Riêng ba LSTM một bước lookback 30 dùng tổng 285 epoch và khoảng 526,233 giây, tương đương 8,77 phút. Từng run đo khoảng 1,18–2,94 giây/epoch. Các điều kiện ghi CPU, float64 và một luồng tính toán. Thời gian giữa các run có biến động, không được dùng như cam kết runtime CNN.

## Chi phí kiến trúc CNN hiện tại

CNN tác giả có 17.057 tham số, LSTM một bước có 4.513, tỷ lệ khoảng 3,78. Trọng số CNN riêng chiếm khoảng 66,63 KiB ở float32 hoặc 133,26 KiB ở float64. Các số này chưa gồm gradient, optimizer, activations, thư viện và dữ liệu, nên không chứng minh mức RAM toàn tiến trình.

Chưa có benchmark train CNN thật. Không suy tốc độ từ tỷ lệ tham số, chưa có thời gian epoch CNN hoặc peak RAM đã kiểm chứng. Dtype CNN còn chờ quyết định.

## Các phương án để quyết định

| Phương án | Số kiến trúc/cấu hình CNN | Run chính thức | Trần epoch | Mục tiêu |
|---|---:|---:|---:|---|
| A | 1 | 3 | 300 | Hoàn thiện CNN và phép so sánh với baseline/LSTM |
| B | 2 | 6 | 600 | So cấu hình hiện tại với một biến thể được định trước |
| C | 3 | 9 | 900 | Khảo sát rộng hơn, thêm chi phí triển khai/giải thích |

Các con số trên đề xuất dùng ba seed 42/123/456 và max100/patience10. Chưa ghi thành quyết định CNN. Tất cả cấu hình dùng cùng 1.954 mẫu train, 250 validation, lookback 30 và scaler của LSTM đối ứng. Ngân sách smoke/test/reload được ghi riêng.

Đề xuất A làm phạm vi khởi đầu, giữ CNN tác giả nếu kiểm contract đạt. Đây là một cấu hình có lý do triển khai, chưa là cấu hình tối ưu. Nếu muốn B/C, xác định cấu hình thử và tiêu chí chọn bằng validation trước training. Khi so độ nhạy kiến trúc giữa hai họ model, cần công bố khác biệt ngân sách đã dùng; ba lookback LSTM cũng là các lần thử đã quan sát validation.

## Cách chốt thời gian trước run dài

Sau khi có CNN hoạt động trên pipeline ở mục 7, chạy smoke giới hạn và đo train, validation, checkpoint, inference, peak RAM trên cùng máy và số luồng. Với E giây/epoch đo được, ngân sách trainer sơ bộ là số run × tối đa 100 × E, cộng overhead đo riêng. Chưa có E của CNN nên hiện không ghi con số phút cụ thể.

Nếu xét CPU float64 chung để so CNN/LSTM, cần đo CNN ở chính dtype đó. Cùng optimizer và giới hạn epoch giúp quy trình nhất quán, nhưng không tự bảo đảm hai kiến trúc tối ưu hoặc có cùng chi phí.

## Nguồn

docs/01_Project_Description_and_Foundation.md mục 9/10, docs/06_Technical_Risks.md, docs/07_Milestones.md, docs/10_Open_Decisions.md, docs/12_Team_Assignment.md, hai summary training TV4 và source CNN đã tiếp nhận.

[Training một bước](../../logs/audit/tv4_item8_20261125T122649342552Z/summary.json) · [Training năm bước](../../logs/audit/tv4_item9_20261125T140320407544Z/summary.json)
