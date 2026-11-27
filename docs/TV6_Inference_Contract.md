# TV6 mục3 — inference research input-only

Module backend/inference/frozen_forecaster.py, class FrozenForecaster(root). Root do server/CLI tin cậy cung cấp, không lấy đường dẫn checkpoint/scaler từ request. Mỗi request kiểm protocol/registry/artifacts mặc định và số Torch threads theo protocol.

```python
from backend.inference.frozen_forecaster import FrozenForecaster
engine = FrozenForecaster(project_root)
rows = engine.predict(forecast_inputs, methods=['lstm', 'cnn', 'persistence'], seed=42)
```

forecast_inputs là list7-field Forecast Input của TV2, raw adjusted_close USD30 phiên. Không nhận target/y/actual hoặc trường lạ. Seed integer42/123/456, mặc định42 như protocol; methods list duy nhất, mode5 chỉ lstm/persistence. Batch có cùng version/horizon, sample IDs duy nhất. Batch order được giữ, không âm thầm sort/drop. Mỗi record phải có đúng30 phiên liên tiếp đã quan sát trong snapshot và raw prices khớp frozen history trong dung sai float64.

Adapter TV3 make_lstm_inputs được dùng lại cho CNN vì cùng logical contract(B,30,1)/CPUfloat64, transpose nằm trong CNN. Không tạo scaler/transforms pipeline mới. Model lấy từ catalog khóa, kiểm loader checksum/provenance/modelmode/run/seed, cache private rồi eval, requires_gradFalse và torch.inference_mode. Chia batch32 giữ tail, inverse_scale bằng scaler train đã lưu. Persistence đọc raw giá cuối input và lặp5 bước, không dùng neural output hoặc target.

Một dòng output cho mỗi sample/method/horizon, gồm protocol ID/hash, dataset/sample/run/model version, scaler, forecast origin/length/step/target_date, predicted_price,currency,feature,result_source. Baseline không có model checkpoint/run/seed, có baseline_version riêng. Không có actual/error/metric trong output. release_id hiệnNone, vì release integration thuộc mục7, không giả bộ đã có release chính thức.

Target dates lấy các phiên tiếp theo từ frozen snapshot, không cộng ngày lịch hoặc dùng future prices làm đầu vào. Scope hiện tại chỉ cho mọi target thuộc validation2023. Yêu cầu chạm test2024–2025, mode không hỗ trợ hoặc thiếu phiên tiếp theo bị từ chối trước load/forward. Chưa có bypass allow_test; đường final test sẽ tích hợp có kiểm chứng ở mục5 sau evaluation mục4. Không hỗ trợ live quote hoặc dự báo ra ngoài lịch snapshot tại mục3.

CLI scripts/check_tv6_inference.py kiểm toàn bộ validation cho9 model và2 baseline modes. Metadata target validation chỉ dùng đối chiếu ngày/horizon ngoài engine, không đưa giá target vào model hoặc tính metric. Script đọc storedX NPZ để so output neural trực tiếp và persistence rawlast. Không train/refit hoặc thay files. Rerun tạo receipt mới, không ghi đè run cũ.

Tests24 integration dùng artifacts thật và validation inputs, kiểm input mutation, repeated inference/modelstate/no-grad, cache/model seeds, invalid records/method/mode, test-date rejection trước forward, no-scaler-fit, protocol rejection trước forward và runtime drift. Kết hợp45 tests evaluation/protocol thành69 tests. Đây không thay thế nghiệm thu final test/release/API hoặc máy khác.


## C?p nh?t TV6 m?c5

Validation l? m?c ??nh. Test2024?2025 ch? qua FrozenForecaster(test_run=...) v?i execution.json ?ang running, ??ng protocol v? ???ng d?n logs/audit/tv6_item5_*/execution.json. Output scope=test, input kh?ng c? target; completed/failed ledger kh?ng d?ng ti?p. Guard local kh?ng ph?i security boundary. CLI scripts/evaluate_tv6_test.py t?o ledger tr??c forward.
