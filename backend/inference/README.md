# inference

**TV6 mục7 hiện tại:** ReleaseForecaster trongrelease_forecaster.py dùng explicitreleaseID aapl-research-residual-v1, LSTMresidual/CNNabsolute vàscaler/decoder riêng. H1lstm/cnn/persistence,H5lstm/persistence,seed42mặcđịnh vàđủ3seed. Input-only, outputreleaseID/SHA, historicaltarget2023–2025cùngsplit; khôngtrain/refit/actual/error/API.14tests vàfullE2Ekhớp20.144predictions. Contract docs/TV6_Release_Contract.md. FrozenForecaster/protocolv1 bên dưới giữlại nhưđường nghiêncứu lịch sử, không tựđổi weights/representation.

Điều phối input, model/baseline và khôi phục giá. Không nhận target, không cập nhật trọng số.

TV6 mục3 có frozen_forecaster.py, FrozenForecaster(root).predict(inputs,methods=[...],seed=42). Chỉ Forecast Input đã kiểm, methods lstm/cnn/persistence (h5 không CNN), không nhận target/y/path/scaler. Protocol/registry/data hashes được kiểm mỗi request, lịch sử input khớp frozen snapshot, CPU64, eval/inference_mode, inverse USD và baseline raw last price. Target dates từ phiên snapshot, không cộng ngày lịch. Không drop batch cuối.

Hiện scope validation2023, chặn test trước load/forward; final evaluator mục5 mới bật đường test có protocol/run audit, không có allow_test tùy tiện. Inference không join actual hoặc tính metrics. release_id=None cho research output trước mục7, không giả release chính thức/API hoàn thành. Không hỗ trợ live data/future dates ngoài frozen snapshot ở mục3. Hướng dẫn docs/TV6_Inference_Contract.md.
