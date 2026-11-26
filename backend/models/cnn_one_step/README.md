# models/cnn_one_step

Mục 4 đã nghiệm thu gradients/Adam với batch 1 và 32, dropout train/eval và state_dict lưu/nạp file thật sau một cập nhật tổng hợp. Bộ CNN/training đạt 102/102 tests, notebook 05 có output. Xem tests/models/test_cnn_learning.py và reports/audits/TV5_Item4_Model_Acceptance.md. Chưa train AAPL trong mục này.

Mục 3 đã forward CNN trên toàn bộ 1.954 mẫu train và 250 validation AAPL cùng bộ dữ liệu LSTM lookback 30/common60. Consumer dữ liệu ở backend/experiments/runner/cnn_data.py, kiểm chứng bằng scripts/check_tv5_aapl_data.py. Đây là model khởi tạo ở eval mode để kiểm shape/dtype/độ hữu hạn.

CNN 1D một bước đã tiếp nhận từ PR #9, commit edc2bd953c7644040f4142a545316377cd143e13. Source gồm model.py và __init__.py, giữ nguyên nội dung tại mục 1.

Baseline tiếp nhận mục 1 có 7/7 tests. Từ mục 2, model dùng CPU float64 tường minh, input hữu hạn (B,30,1), output (B,1). Kiến trúc hai Conv1d 1→16→32 kernel3, MaxPool2, Dropout0,1 và Linear480→32→1, vẫn 17.057 tham số. Config khóa lookback 30, một feature/một output và kiểm giá trị không hợp lệ. Model từ chối input sai dtype, không tự cast hoặc đổi global dtype.

Chạy `python -m pytest tests/models/test_cnn_one_step.py tests/models/test_cnn_contract.py tests/models/test_cnn_learning.py tests/training -q` trong môi trường có dependencies theo lock TV4. Tới mục 6, bộ hồi quy đạt 138/138. Notebook 05 lưu output dữ liệu/forward, gradient/Adam/dropout/state_dict và runner/checkpoint tổng hợp. Persistence CNN ở backend/artifacts/cnn_checkpoint.py, còn smoke AAPL ở mục 7 và official runs mục 8. Chưa có kết luận chất lượng CNN trên AAPL.
