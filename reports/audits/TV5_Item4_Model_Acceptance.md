# TV5 mục 4 — nghiệm thu model CNN

Ngày 26/11/2026. Giữ kiến trúc phương án A và CPU float64 đã chốt. Không đổi source model, dữ liệu hoặc training loop TV4.

## Phạm vi kiểm chứng

- Batch 1 và 32, MSE backward tạo gradient hữu hạn và khác 0 trên từng tensor tham số. Adam learning rate 0,001 thay đổi từng tensor, trọng số còn hữu hạn. zero_grad xóa gradient.
- Dropout train tạo mask ngẫu nhiên, có phần tử bị loại và hệ số giữ đúng. Eval bỏ dropout và forward lặp lại cho cùng output.
- Sau một Adam step bằng tensors tổng hợp, lưu config/state_dict ra file thật, nạp weights_only vào instance mới và so output eval với dung sai bằng 0. Strict load từ chối state_dict thiếu key.
- Chạy lại contract CNN và bộ training TV4 để phát hiện hồi quy.

Tests mới ở `tests/models/test_cnn_learning.py`. Notebook 05 mục 4 gọi pytest, lưu JUnit, stdout và receipt có môi trường, lệnh chạy, số tests. Kết quả nghiệm thu được ghi sau khi notebook thực thi thành công.

## Kết quả thực thi

Notebook 05 đã chạy 6/6 code cell, 9 cells tổng cộng. Bộ CNN/training đạt 102/102 tests, không skip. Receipt notebook ở `logs/audit/member_notebooks_20261126T034910658036Z/summary.json`; receipt pytest và JUnit ở thư mục `tv5_item4_*` được in trong cell mục 4.

Một lượt chẩn đoán terminal trong sandbox đạt ba ca nhưng không tạo được pytest temp ngoài workspace cho ca file roundtrip, WinError 5. Đây là lỗi quyền môi trường, không tính lượt đó là đạt. Lượt notebook có quyền chạy kernel phù hợp đã kiểm đầy đủ cả roundtrip và bộ hồi quy thành công.

Đây là diagnostic bằng dữ liệu tổng hợp, không chứng minh chất lượng dự báo hoặc không overfit trên AAPL. State_dict ở đây chưa phải checkpoint phát hành có provenance, optimizer resume hoặc tích hợp trainer. Các phần đó thuộc mục 5/6, smoke AAPL thuộc mục 7.
