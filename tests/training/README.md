# Kiểm tra dự kiến: training

Gradient/update, validation không update, checkpoint/early stopping.

TV4 mục1: ba file test_experiment_manager.py, test_experiment_runner.py và test_training_loop.py tiếp nhận từ PR#10. Chạy scripts/run_tv4_checks.py --require-clean để lưu JUnit/pytest/environment/source evidence; không alias import hoặc lấy code từ checkout audit.

Tests dùng tensors tổng hợp và mock checkpoint, các ca early stopping dùng loss mô phỏng. Evidence xem reports/audits/TV4_Progress.md.

Mục2: `test_tv4_float64_contract.py` bổ sung36 cases trên cả hai model TV3: bảo toàn giá trị NumPy64, không đổi global dtype, không silent cast, CPU/shape/horizon guards, batchB1, Adam buffers/gradients/weights64 và validation không đổi weights/gradients. Có train_model thật nhưng checkpoint hook được mock rõ ràng. Tổng suite52 cases ở thời điểm mục2; chưa là bằng chứng training AAPL/checkpoint thật.
