# Phân tích lỗi và giới hạn

Trạng thái27/11/2026: TV6 mục6 đã hoàn thành phân tích local; còn vấn đề mô hình cần xử lý trước khi chốt candidate/release. Không train/fix thêm trong mục6.

## Nội dung cần hoàn thiện

LSTM v1 đã thực hiện dự báo và đánh giá test2024–2025 nhưng thua persistence. Sai lệch âm và lỗi tăng theo mức giá cao là phát hiện trọng tâm; không chỉ một vài shock. Trên482/502phiên test không vượt ngưỡng95% absreturn của train, MAE LSTM h1 mean3seed vẫn10,801USD so persistence2,112USD. Các tháng10–12/2025 có lỗi LSTM cao nhất; không gán nguyên nhân sự kiện thị trường khi chưa có nguồn xác minh.

Phiên bản residual cải thiện trên development2022/2023, nhưng chưa có test độc lập mới. Kiểm độ nhạy12checkpoint LSTM trên development cho thấy: h1fold2023 realhistoryMAE1,619409USD so flathistory1,619649USD; dự báo khác trung bình0,003708USD. Delta dự báo gần+0,224USD vớistd theo thời gian0,00454USD. Bằng chứng phù hợp với hiệu chỉnh gần hằng số, chưa chứng minh30phiên đóng góp tín hiệu mạnh. Fold2022h1 nhạy hơn, nên không khái quát thành mọi LSTM bỏ qua lịch sử.

H5fold2023 realMAE2,931102USD so flat2,928293USD; bản residual còn kém baseline ởfold2022h5. Lợi thế tổng thể nhỏ/không đồng đều. Cần kiểm tham chiếu drift fit train và gradient/ablation trước khi tăng độ phức tạp; đây mới là hướng đề xuất, chưa thực hiện sửa.

Giới hạn: snapshot giá adjusted hồi cứu không là point-in-time; một cổ phiếu/một feature; ngân sách kiến trúc khác nhau; validation đã dùng chọncheckpoint; input nhân tạo có thể ngoài phân phối; h5windows chồng lấn; stress dùngactual gán nhãn hồi cứu, không là feature dự báo. Không có phép kiểm significance/threshold thực tiễn được khóa, không suy kết quả thành lợi nhuận. Test cũ đã quan sát trước phát triển residual, không được tái gắn nhãn độc lập.

Kiểm ưu tiên1 sau mục6 đã hoàn tất: LSTM h1development2023MAE1,619409USD so tham chiếu drift chỉfittrain1,631012USD.108gradientprobes trên12checkpoint/init/batches xác nhận checkpointcore còn nhận gradient và đã đổiweights. Gradient trên relativeinput cũ nhỏ hơn phiên gần khoảng1e-6–1e-7 trênbatchkiểm; chưa phải chứng minh vanishinggradient trong toàn bộ quá trình train. Không có optimizerstep/model mới hoặc sửađứtbackprop. [Báo cáo kiểm đường học](audits/TV6_LSTM_Learning_Check.md). Notebook hiện30cells/15code cells cóoutput; ablation sửa yếu tố mô hình chưa thực hiện.

## Bằng chứng

[Hoàn thành chốt ứng viên không train thêm](audits/TV6_LSTM_Candidate_Completion.md):18pipelinechecks,84metrics/21aggregates được audit. Residual last đánhgiá sau pháttriển trên testđãquan sát cóMAE2,465892USD(h1),4,607636USD(h5overall), nhỉnh hơnpersistence2,476989/4,632497. Lợi thế nhỏ, khôngđộc lập hoặc significanceclaim. Catalogv1 giữnguyên; registry mới làứngviên cho mục7. Notebook38cells/19code cells cóoutput.

[Ablation readout LSTM h1](audits/TV6_Readout_Ablation.md):6run giữ mọi điều kiện ngoài readout. Meanreadout tăng ảnh hưởng gradient về lịch sử cũ nhưng độ chính xác kém ở2022, chỉ nhỉnh rất ít ở2023. Không chọn thay last residual, không mở testforward mới. Không coi gradient lớn hơn là bằng chứng mô hình tốt hơn. Notebook hiện34cells/17code cells cóoutput.

[Báo cáo mục6 và ưu tiên xử lý](audits/TV6_Item6_Error_Analysis.md), [kết quả residual](audits/TV6_Residual_Development_Results.md), [test v1](audits/TV6_Item5_Test_Evaluation.md).

Receipt `logs/audit/tv6_item6_20261127T015255603485Z/summary.json`, audit độc lập cùngfolder:31metric test khớp gốc,73summaryrows,168probe metrics/35.592probe predictions, partition đầy đủ, source/weights bất biến.4tests mới đạt. Notebook06:26cells/13code cells có output thật. Không forward test mới hoặc updateweights trong mục6; chưa xác minh máy thành viên khác.
