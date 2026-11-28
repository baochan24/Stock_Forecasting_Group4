# TV6 mục10 — audit toàn bộ coursework và chốt đầu ra

**Bổ sung hoàn thiện cùng ngày:** cài mới từ lock và kiểm trên venv độc lập đã đạt85 pins/pip check,62 tests API/handoff,14 checks Chrome và5 tests JS. Có bảng CSV và công cụ xuất biên bản cho người nhận. [Báo cáo hoàn thiện](TV6_Closure_and_Handoff.md). Các nhận xét “chưa fresh install” trong lượt audit ban đầu bên dưới là lịch sử; máy thành viên khác và quyền phân phối dữ liệu vẫn chưa được xác nhận.

Ngày28/11/2026. Đã đối chiếu `docs/đề_yêu_cầu.md`, `docs/yêu_cầu_mẫu_đề_tài.md`, rule, module/data contracts, phân công và bằng chứng ở workspace chính. Không dùng checkout lồng để suy trạng thái, không train/tune/refit model hoặc sửa kết quả bất lợi.

## Kết luận

**Đã triển khai và kiểm chứng local bài toán chính và hai extension của đề:** dùng chuỗi30phiên adjusted close AAPL để dự báo phiên tiếp theo bằng LSTM; LSTM5phiên; CNN1D so với LSTM cùng pipeline. Đầu ra gồm giá dự báo USD,ngày target,model/run/seed/release và metric đối chiếu persistence/actual. API/frontend dùng model đã train, không nhận target vào model.

**Chưa ký nghiệm thu toàn bộ bàn giao:** cài mới trên cùng máy đã đạt ở lượt bổ sung; vẫn cần máy thành viên khác, quyền phân phối dữ liệu hoặc nguồn thay thế được chấp thuận và định dạng/lịch nộp cuối. Không có bằng chứng để tuyên bố LSTM vượt baseline độc lập/bền vững hoặc có lợi nhuận.

## Audit flow và kết quả

| Phần | Đã kiểm | Kết luận |
|---|---|---|
| TV1 | Version/hash/provenance/raw–validated/quality,2766 phiên | Đạt local; quyền dữ liệu/máy nhận còn mở |
| TV2 | Scaler2014giátrain,prepared/split/date/float64,temporal audit | Đạt; không refit hoặc target vào inference |
| TV3 | LSTM H1/H5,shape/dtype/trace/gates/strict reload | Đạt kỹ thuật; không tự chứng minh hiệu quả dự báo |
| TV4 | Shared training/early stopping/checkpoint/config/seed/history | Có model gốc đã khóa và bằng chứng; audit không train thêm |
| TV5 | CNN H1 cùng cohort/pipeline,3seed,configuration/reload | Đạt; ngân sách tuning khác LSTM phải công bố |
| TV6 evaluation | Original test và residual post-development tách phase,USD/per-horizon/mean/std | Metric có đối chiếu; không giấu persistence thắng bản gốc |
| API/UI | Hash release/sidecar,20.144 stored rows,request/metric/trace,5JS/14Chrome checks | Đạt local theo receipt/source đã khóa |
| Reports/setup | Bảy phần báo cáo được cập nhật,ma trận10 nội dung đăng ký,hướng dẫn thành viên | Có nội dung hiện hành,không còn dùng khung cũ để tuyên bố hoàn thành |
| Runtime handoff | Gói web mới giữ đường dẫn,manifest/checksum/verifier; xác nhận giải nén riêng | Xem receipt bàn giao riêng; không thay thế máy khác |

## Kiểm thử và phạm vi bằng chứng

- Core JUnit `logs/audit/tv6_item10_core_verified_20261127.xml`:664 cases gồm subtests,0 failures/0 errors,7 skips vì thiếu biến TV1_DATASET_VERSION. Đây không phải664 test functions độc lập.
- Các ca artifact/handoff TV1 thật được chạy lại với version cụ thể: `logs/audit/tv6_item10_real_tv1_20261128.xml`,10passed,không bỏ qua.
- Hai suite acquisition offline:9/9đạt bằng `.venv/tv1_clean` có yfinance; receipt/log `logs/audit/tv6_item10_acquisition_20261128.*`.
- Không cộng các số trên thành tổng unique tests vì có ca được chạy lại. Các optimizer tests dùng fixture tổng hợp; không tạo model nghiên cứu mới hoặc thay weights đã khóa.
- Lần chạy gộp ban đầu thiếu yfinance trong môi trường model; lần sandbox tiếp theo lỗi quyền thư mục temp. Đó là lỗi môi trường có log/XML riêng,không tính đạt. Đã giải quyết bằng môi trường đúng vai trò và thư mục temp riêng,không cài chồng dependencies.
- Audit cuối đọc hash120file tiếp nhận,scaler/prepared thật,rawactual/sessiontarget,metric scalar math và receipt test gốc/residual; summary/coverage/comparison/per-horizon ở folder được `logs/audit/tv6_item10_latest.json` chỉ tới. Source/artifacts của release v1 giữ nguyên.

## Kết quả khoa học cần giữ

Test gốc2024–2025,mean3seed: LSTM H1 MAE10.896342/RMSE14.031708USD;CNN H1 8.162562/10.073087; persistence2.476989/3.654583. LSTM H5overall12.603942/16.155448 so persistence4.632497/6.707243. **Persistence tốt hơn model gốc.**

Residual phát triển sau khi quan sát test cũ: H1mean3seed2.465892/3.652078;H5overall4.607636/6.682840. So với persistence cùng các cohort502/498 windows,lợi thế nhỏ. Đây là post-development old test,không phải holdout mới. Bằng chứng độ nhạy còn yếu,không nói đã học quy luật thị trường mạnh. Từngseed/std mẫu/per-horizon nằm trong CSV và reports06.

## Phát hiện và xử lý ở mục10

1. Reports01/05 còn placeholder; reports02/03/04/06/07 có trạng thái cũ trộn tiến độ. Đã bổ sung tổng kết hiện hành,giữ lịch sử có nhãn rõ.
2. ZIP mục7 thiếu API/frontend/sidecar. Thêm builder/verifier gói runtime web local,không sửa ZIP/release cũ hoặc tự upload.
3. Browser checker mục9 gắn interpreter máy leader. Hướng dẫn đã nói rõ giới hạn; verifier gói web dùng chính `sys.executable` của môi trường người nhận.
4. Không có xác nhận máy khác/quyền phân phối công khai. Ghi còn mở thay vì đánh dấu hoàn tất giả. [Trạng thái dữ liệu và nguồn](../../docs/TV6_Data_Use_and_Limits.md).
5. Đọc CSV bằng parser mặc định có thể lệch bit cuối so với API; auditor dùng cùng `float_precision='round_trip'`,không đổi data hoặc nới kiểm giá để che sai lệch.

## Output nộp và bảo vệ

Xem [ma trận đầu ra/10 nội dung đăng ký/7 báo cáo](../../docs/TV6_Coursework_Output_and_Defense.md), [cài chạy thành viên](../../docs/TV6_Member_Setup_and_Run.md), notebook06 mục10. Gói runtime không kèm `.git`,venv,secrets hoặc toàn bộ prepared/research logs; notebook trong gói để đọc saved outputs,RunAll toàn nghiên cứu cần artifacts nghiên cứu gốc. Không gọi gói runtime là toàn bộ hồ sơ tái tạo training.

Không push/merge/upload hoặc triển khai Internet trong mục này. Local technical audit đã thực hiện; trạng thái nghiệm thu toàn bộ vẫn có điều kiện mở nêu trên.
