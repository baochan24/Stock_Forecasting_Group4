# Xử lý ưu tiên1 — tham chiếu train-only và kiểm đường học LSTM

Hoàn thành local27/11/2026 theo yêu cầu tiếp tục bước sửa sau mục6. Bước này bổ sung hai phần kiểm chứng còn thiếu trước khi thay mô hình: **tham chiếu drift fittrain và đo gradient**. Không huấn luyện mới hoặc tuyên bố model đã cải thiện thêm; không optimizerstep/đổicheckpoint/testforward.

## Đối chiếu với điều chỉnh hằng số học từ train

Tham chiếu origin+mean(target−origin) ước lượng riêng từnghorizon từ cácwindow **train** trước mỗifold, không dùngactual validation để tính drift. Fold2022 fit đến2021; fold2023 fit đến2022. Bộ dữ liệu/keys validation giữ nguyên và đủba seed LSTM.

MAE USD, LSTM là mean3seed; H5overall flatten mọi sai số trướcmetric:

| Validation | Horizon | Persistence | Train-meanchange | LSTM residual |
|---|---|---:|---:|---:|
| 2022 | 1 | 2,602120 | 2,607913 | 2,596975 |
| 2022 | 5overall | **4,313107** | 4,345204 | 4,323299 |
| 2023 | 1 | 1,636779 | 1,631012 | 1,619409 |
| 2023 | 5overall | 2,984996 | 2,955910 | 2,931102 |

RMSE2023h1: persistence2,120593; drift2,115272; LSTM2,106283USD. H5overall:3,903600/3,869214/3,841833USD. LSTM tốt hơn tham chiếu drift này trên cả4task/fold, nhưng chênh lệch nhỏ; h1fold2023 chỉ0,01160USD MAE, khoảng0,71%. Không phải tuyên bố significance hoặc hiệu quả thực tiễn.

Drifth1 ước lượng train: +0,083746USD chofold2022,+0,050085USD chofold2023. LSTM h1fold2023 dự báo mức điều chỉnh trung bình khoảng+0,224USD theo kiểm tra trước. Không lấy giá trịvalidation này làm tham chiếu fit; không coiflatLSTM là train-meanchange vì chúng là hai đại lượng khác nhau.

Kết hợp phép thửflat trước đó (realMAE1,619409 vsflat1,619649): LSTM thắng một tham chiếu drift đơn giản **chưa chứng minh lợi ích đó đến từ biến động lịch sử**. Không thay persistence chính thức bằng tham chiếu chẩn đoán này để thay đổi kết luậnv1.

## Đường học không bị đứt ở các checkpoint kiểm

12checkpoint residual hiện có ×3trạng thái ×3batch train cố định first/middle/last32 =108backwardprobes. Mỗi phép đo dùng **bản sao riêng**, lossMSE theo delta chuẩn hóa hiện tại, khôngoptimizer. State/mode/grad của model gốc không thay đổi; file checkpoint/hash trước/sau giữ nguyên.

- Tất cả36batch của12checkpoint hiện có cho coregradient hữu hạn vànonzero. GradientL2 core theo nhómfold/horizon cómin khoảng3e-6 đến8,5e-5. Đây không phải ngưỡng chất lượng mà là xác nhận kết nối trên cácbatch kiểm.
- Coreweights của12checkpoint khác khởi tạo tái dựng cùngseed với L2delta0,5076–4,6773. Tái dựng init theo source/seed, không phải archived initialstate; hỗ trợ kết luận đã có cập nhật, không tái lập toàn bộ trajectoryoptimizer.
- Zerooutputhead làm core/inputgradient=0 khi headweights còn0 tại backwardkhởi tạo; headgradient vẫn có. Defaultheadkhởi tạo có coregradientnonzero. Không suy ra core bị khóa suốt quá trình train, hoặc đổihead chắc chắn tăng độ chính xác.
- Norm ở những trạng thái cóloss/thangđo/sốtham số khác nhau không được so đơn giản để kết luận vanishinggradient. Phép đo không thay thế loggradient trong lúc train.

## Bằng chứng ưu tiên thông tin gần

Mean gradientL2 theo từngtọa độrelativeinput của checkpoint trên cácbatchtrain; chỉ so vị trí trong cùng nhóm, không phải totalderivative theo rawprice/anchor:

| Fold/task | Gradient vị trí1 | Gradient vị trí29 | Tỷ lệ1/29 |
|---|---:|---:|---:|
| 2022h1 | 8,46e-11 | 7,36e-5 | 1,15e-6 |
| 2022h5 | 2,01e-12 | 2,45e-5 | 8,22e-8 |
| 2023h1 | 8,55e-12 | 6,58e-6 | 1,30e-6 |
| 2023h5 | 5,57e-12 | 7,81e-5 | 7,13e-8 |

Vị trí1 là phiên cũ nhất,29 là phiên trướcorigin; bỏ vị trí30 khỏi biểu đồ diễn giải vìrelativeinput cuối luôn0 theo định nghĩa. Gradient theo thời gian giảm mạnh về quá khứ trên probes, phù hợp với độ nhạy tập trung lịch sử gần. Chưa đo cơ chếgate hoặc chứng minh đây là nguyên nhân duy nhất của sai số.

Không buộc mạng dùng đủ30phiên bằng mọi giá: nếu chuỗi cũ không có tín hiệu, tăng độ nhạy có thể làm dự báo tệ hơn. Bước sửa phải được chấm bằngvalidationMAE/RMSE vàổn định, không bằnggradient lớn hơn hoặc đồ thị phức tạp hơn.

## Kết luận và hướng sửa cụ thể sau kiểm chứng

Không phát hiện lỗi đứtbackprop để cần vá trainingloop. Giữ hướng LSTM residual và kiến trúc hiện có làmcontrol. Nút thắt còn lại là **giá trị thông tin chuỗi yếu trong các checkpoint đã chọn**, không phải chắc chắn model không train được.

Bướcablation tiếp theo nên có ngân sách cố định, ưu tiênh1, giữsampler/cohort/seeds/lr, thay từng yếu tố liên quan khởi tạo/đọc lịch sử và loggradient trong quá trình train. Phải đối chiếu thêmflat vàtrain-onlydrift; không chỉ kiểm thắngpersistence. Chưa chọn cấu hình sửa dựa vào norm snapshot, chưa tăngepoch/layers/lr hoặc triển khaiablation trong bước này. Giữ nguyên kết quảtest đã công bố; không promote release/demo.

## Kiểm chứng, notebook và tái lập

7tests mới đạt: h1/h5 tính taymeanchange vàpredictinput-only, chặnval/futurecutoff/version/duplicate, zeroheadgradient và không sửa caller. JUnit `logs/audit/tv6_lstm_learning_tests.xml`.

Audit độc lập đạt4reference/4fullpairedcohorts/70metricrows/108gradientbatches. Reference được đối chiếu bằngmath.fsum từ nguồntrain, metric bằngscalarerrors; actual/origin/keys validation khớpsource, đủba seed, source/scaler/checkpointhashes giữ nguyên.

Receipt `logs/audit/tv6_lstm_learning_20261127T020707964054Z/summary.json`; `independent_audit.json`, CSV/referenceJSON/2PNG vànotebook_verification cùngfolder. Scripts `check_tv6_lstm_learning.py`, `audit_tv6_lstm_learning.py`; plan `experiments/configs/tv6_lstm_learning_check_v1.json`. Không sinh checkpoint model mới.

Notebook06 hiện30cells/15code cells cóoutput, giữ nguyên26cells trước; thêm bảng từngseed/horizon, tham chiếu drift và gradient/parameterdelta, biểu đồ inputgradient. Run All chỉ đọc kết quả đã lưu, không backward hoặctrain. Chưa xác nhận máy thành viên khác.
