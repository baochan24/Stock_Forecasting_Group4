# baselines

Persistence dùng giá gốc cuối input. Một bước ra một giá; năm bước lặp lại cùng giá đó. Không training.

TV5 mục9 bổ sung persistence.py như dependency dùng chung cho phép so sánh. predict_persistence chỉ nhận input raw USD (B,T,1), trả (B,1) hoặc (B,5) bằng giá cuối input, không nhận target hoặc fit. Kiểm dữ liệu finite và không mutate. Chưa là nghiệm thu toàn bộ baseline/inference/release TV6.
