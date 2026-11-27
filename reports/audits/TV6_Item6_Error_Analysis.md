# TV6 mục6 — phân tích lỗi LSTM và báo cáo trước khi sửa tiếp

Hoàn thành phân tích local27/11/2026 theo yêu cầu người dùng: **báo cáo vấn đề trước, chưa train/fix tiếp**. Mục6 có đầu ra và bằng chứng; điều đó không có nghĩa mô hình đã đạt hiệu quả vượt persistence để nghiệm thu release.

## Phạm vi và cách kiểm

1. Phân tích lại prediction/test residual v1 đã lưu: monthly/yearly, rolling20phiên, từnghorizon/overall, top10errors mỗi nhóm, stress theo ngưỡng95% thay đổi giá tương đối **fit trên train**.
2. Reload12checkpoint residual LSTM đã có (2fold×h1/h5×3seed), chỉ forward trên development2022/2023. So lịch sử thật với cửa sổ phẳng, đảo/xáo trộn29phiên trước; giữ nguyên giá cuối vàRNG20261127. Không optimizer/backward/updateweights, không fit scaler, không testforward mới.
3. Kiểm source/hash/provenance, realforward khớp prediction đã lưu, state trước/sau bằng tuyệt đối. Metric dùng evaluation.one_step; audit độc lập dùng math.fsum/sqrt để đối chiếu. Dùng đủ3seed, không chọn model/control theo điểm đẹp nhất.

## Phát hiện1 — residual h1fold2023 chủ yếu hiệu chỉnh gần hằng số

Mean3seed trên đúng250phiên validation2023:

| Lịch sử đưa vào LSTM h1 | MAE USD | RMSE USD | Mean abs khác biệt dự báo so lịch sử thật |
|---|---:|---:|---:|
| Lịch sử thật | 1,619409 | 2,106283 | 0 |
| Phẳng, toàn30giá bằng origin | 1,619649 | 2,106067 | 0,003708USD |
| Đảo29giá trước | 1,617603 | 2,105731 | 0,017801USD |
| Xáo trộn29giá trước | 1,618488 | 2,105813 | 0,009611USD |

Với lịch sử thật, phần điều chỉnh dự báo có mean+0,2242USD nhưngstd theo thời gian chỉ0,00454USD, so std actualchange2,1058USD. Cửa sổ phẳng cho một mức điều chỉnh hằng số theo từngseed/horizon, mean3seed+0,2253USD. Bỏ diễn biến lịch sử gần như không làm mất lợi thế MAE; RMSE phẳng còn hơi thấp hơn. Kết quả phù hợp với dự báo gần **origin+drift nhỏ**, chưa thể quy lợi thế so persistence cho khả năng học quy luật30phiên mạnh.

Không kết luận LSTM tuyệt đối bỏ qua lịch sử: ởfold2022h1, meanabsđổi dự báo real→flat là0,1741USD; đảo/xáo trộn làm MAE tăng. Mức sử dụng lịch sử khác giữa fold. Các input nhân tạo có thể ngoài phân phối, nên đây là sensitivity diagnostic, không phải causal ablation hoặc giả lập thị trường thực. Tuyệt đối không chọn reverse/shuffle làm phương án cải tiến chỉ vì điểm validation thấp hơn.

## Phát hiện2 — năm bước cũng chưa chứng minh đóng góp chuỗi rõ

Validation2023h5overall: realMAE2,931102/RMSE3,841833; flatMAE2,928293/RMSE3,839706. Meanabsđổi dự báo chỉ0,03412USD. Từnghorizon phần điều chỉnh cómean khoảng+0,153/+0,264/+0,339/+0,396/+0,487USD; std theo thời gian0,050/0,056/0,064/0,034/0,010USD, nhỏ so std actualchange2,12–4,96USD. Không dùng std overall trộn5horizon để suy sensitivity theo thời gian.

MAE residual2023 từh1đếnh5 là1,640/2,408/3,043/3,558/4,007USD; baseline cùngcohort1,655/2,431/3,099/3,623/4,117USD. Chênh lệch nhỏ. Đây là h1 bên trong model5đầu ra, không đồng nhất modelh1riêng (cohort250vs246).

Fold2022h5real4,323299USD còn hơi kém persistence4,313107USD. Lợi thế không bền vững trên hai năm. Không đặt practical-significance threshold sau khi xem điểm; chưa có phép kiểm significance được khóa, h5windows chồng lấn.

## Phát hiện3 — lỗi v1 không chỉ do các phiên shock

LSTM h1testv1 mean3seedMAE2024=7,3686USD,2025=14,4523USD; bias tương ứng−6,5985 và−13,8287USD. Những tháng lỗi cao nhất:12/2025=31,7622;11/2025=29,7115;10/2025=23,2907USD. Persistence có tháng cao nhất04/2025=6,3518USD; không cùng kiểu lỗi cuối2025 của LSTM.

Ngưỡng stressh1 lấy từtrain2015–2022: absreturn>3,7502%. Test có20phiên vượt ngưỡng,482phiên còn lại. Trên482phiên này, MAE LSTM vẫn10,8010USD so persistence2,1119USD. Vì vậy “chỉ vài phiên biến động lớn làm model thua” không phù hợp với bằng chứng. Kết quả củng cố chẩn đoán bias/ngoại suy mức giá ởv1; không chứng minh nguyên nhân duy nhất.

Ví dụseed42 ngày02/12/2025: actual285,1964USD,forecast244,5256USD,lỗi40,6708USD. Ví dụ lấy bằng quy tắc top10, không tự gán nguyên nhân tin tức. Không xóa/sửa/loại ngày này khỏi dataset để cải thiện metric.

## Phát hiện4 — khả năng chống shock của bản mới còn ít bằng chứng

Ngưỡngtrain củafold2023 cho validation2023h1 chỉ có2phiên stress: MAE residual8,3446USD,baseline8,3439USD. H5 có15**error rows**,không phải15sự kiện độc lập; MAE12,1275 so11,9853USD. Điểm tổng thể tốt hơn chưa chứng minh mô hình xử lý shock tốt hơn.

Fold2022h1 có27phiên stress, residual6,8200 so persistence6,9007USD; nhưng nhóm224phiên còn lại residual2,0879 so2,0840USD. Cần đánh giá ổn định qua thời gian, không chỉ nhìn overall.

Stress dùng actual tương lai để phân nhóm **hồi cứu**, không đưa vào input hoặc chọn model trước phiên dự báo. Không thay nhãn này thành feature để đánh giá giả tạo.

## Phát hiện5 — bằng chứng cải tiến và nguyên nhân cần phân biệt

Thử nghiệm trước có cải thiện thực trên development so đối chứng train lại. Nhưng thay đồng thời relativeinput/deltatarget/zerohead, và sampler/common60 của control mới khácv1. So sánh ghép cặp mới là hợp lệ trong phạm vi đó; không đủ cô lập tác động riêng từng thay đổi hoặc khẳng định đã chữa testv1.

Test2024–2025 đã được quan sát trước khi thiết kế residual. Không có kết quả test độc lập cho candidate này; không train/tune theo test rồi công bố như test mới. Mục6 không thay weights/catalog/demo/release.

## Vấn đề cần xử lý ở bước sửa tiếp, theo thứ tự

| Ưu tiên | Vấn đề đã thấy | Hướng kiểm chứng/sửa đề xuất — chưa thực hiện |
|---|---|---|
| 1 | Residual gần drift hằng số, chưa chứng minh giá trị lịch sử | Thêm tham chiếu drift chỉ ước lượng trêntrain; đo gradient/head/core và sensitivity trên input thật. Không chọn drift theo actualvalidation/test. |
| 2 | Chưa biết yếu tố nào trong gói cải tiến tạo lợi ích | Ablation có ngân sách cố định, giữ sampler/cohort/seeds; đổi một yếu tố mỗi lần. Kiểm zerohead/khởi tạo và thang delta bằng bằng chứng gradient trước khi quyết định. |
| 3 | Lợi thế baseline nhỏ/không đồng đều, ítshock2023 | Bổ sung walk-forward trong miền development và báo đủfold/seed/horizon, không chọn năm thắng. |
| 4 | Không có kiểm chứng độc lập cho thay đổi sau test | Chốt protocol mới trước một tập tương lai chưa dùng để định hướng phát triển; mọi táiđánhgiá test cũ phải ghi exploratory/post-test. |

Không có bằng chứng hiện tại để khẳng định vanishinggradient/gatesaturation hoặc đơn giản tăngepoch/layers/lr sẽ sửa được. Bestcheckpoint h1residualfold2023 ởepoch3/4/3; điều này là quan sát, chưa xác định nguyên nhân. Không tăng độ phức tạp CNN trong bước sửa tập trung LSTM.

## Kiểm chứng và đầu ra

- 4tests mới đạt: controls giữ origin/multiset và deterministic, metric tính tay/rolling/stresspartition, duplicatekeys, h5keys vàoverall; `logs/audit/tv6_item6_tests.xml`.
- Audit độc lập đạt:31metric test gốc không đổi,73summaryrows,168probe metric rows,35.592probe prediction rows; monthly/yearly/stress partition đủ số lỗi; flat correction hằng số từnghorizon;12models/state vàsourcehash giữ nguyên.
- Notebook06 có26cells/13code cells có output; bổ sung bảng từngseed, sensitivity scatter/flatcompare, month/rolling vàhorizoncharts. Giữ output các mục trước; builder đồng bộ.
- Receipt `logs/audit/tv6_item6_20261127T015255603485Z/summary.json`; CSV/PNG/audit độc lập cùngfolder; `notebook_verification.json`. Scripts `analyze_tv6_item6.py`, `audit_tv6_item6.py`.

**Kết luận cá nhân:** LSTM vẫn đúng trọng tâm đề, nhưng candidate hiện tại chưa cho thấy học chuỗi mang giá trị rõ hơn hiệu chỉnh đơn giản. Nên xử lý ưu tiên1trước khi tuning kiến trúc hoặc nghiệm thu model cho release. Mục6 phân tích đã hoàn thành; bước tiếp theo theo người dùng là sửa các vấn đề sau báo cáo, chưa chuyển sang mục7.
