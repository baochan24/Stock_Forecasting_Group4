# TV5 mục 5 — nối CNN vào training loop TV4

Ngày 26/11/2026. Mục này phục vụ phần Extension CNN vs. LSTM trong đề. Giữ phương án A, CPU float64, 30 phiên/một feature/một target. Không thay source trainer TV4 hoặc kết quả các run cũ.

## Thay đổi

`cnn_factories.py` kiểm schema CNN, tạo model và dùng lại consumer/loader TV4. Adapter config chỉ đổi schema để gọi data factory, không tạo mạng LSTM hoặc sửa dữ liệu. YAML CNN ghim cùng snapshot/scaler/prepared hashes, common-history và ba seed đã chốt. Adam 0,001, MSE, batch 32, tối đa 100 epoch và patience 10 là ngân sách cấu hình chính thức, chưa chạy trong mục này.

Runner kiểm config và dispatch factory theo model_type. CNN đi qua cùng train_model/_run_epoch, weighted epoch loss, validation no_grad, early stopping và khôi phục best weights trong RAM. Persistence CNN bị từ chối trước khi tạo run nếu chưa chọn RAM diagnostic; checkpoint có provenance thuộc mục 6.

Thay đổi runner có bản trước sửa tại `logs/audit/tv5_item5_source_before/`. Hash được ghi trong `TV5_Item5_Source_Changes.json` để đối chiếu thay đổi có chủ đích với intake TV5. Không thay source TV1–TV3 hoặc trainer TV4.

## Kiểm chứng

Chín ca tích hợp trong tests/training/test_cnn_runner.py kiểm từ chối config horizon/lookback/common-history/output/optimizer sai, dữ liệu config không bị sửa, factory đúng CNN, validation loss theo số mẫu và giữ batch cuối 1 mẫu, không gradient/không đổi trọng số, runner RAM một epoch và fail-fast persistence.

Một ca chạy backward/Adam thật qua trainer CNN, thay giá trị validation bằng plateau có kiểm soát để kiểm patience và restore best state. Giá trị plateau không phải metric chất lượng mô hình. Dữ liệu train trong các tests là tensors tổng hợp. Notebook kiểm thêm loader AAPL thật nhưng chưa train AAPL hoặc đánh giá test.

Một lượt terminal sandbox bị WinError 5 với pytest basetemp. Không tính lượt lỗi môi trường là đạt; kết quả nghiệm thu dựa trên lượt notebook có quyền chạy kernel phù hợp.

## Kết quả hồi quy

Bộ CNN/training đạt 111/111 tests, trong đó chín ca tích hợp mới. Receipt ở `logs/audit/tv5_item4_20261126T040313538100Z/summary.json`, JUnit cùng thư mục. Cell mục 4 chạy lại toàn bộ tests nên receipt mang prefix item4; cell mục 5 trích chín ca mới và lưu receipt riêng.

Notebook 05 chạy 7/7 code cell, tổng cộng 11 cells, đã lưu output local. Receipt thực thi `logs/audit/member_notebooks_20261126T040231598369Z/summary.json`. Loader thực xác nhận 1.954 train, 250 validation, batch cuối 2/26 mẫu và drop_last=False.

Bước tiếp theo là mục 6, checkpoint CNN cùng provenance và kiểm reload.
