# Release nghiên cứu TV6 — hợp đồng và cách sử dụng

Ngày27/11/2026, releaseID **`aapl-research-residual-v1`**. Đây là bộ inference lịch sử cục bộ, chưa phải API hoặc website. Không cần train lại.

## Bộ phát hành

- Manifest: `artifacts/releases/aapl-research-residual-v1/manifest.json`.
- Registry ghim manifestSHA/semanticSHA: `experiments/configs/tv6_research_release_v1.registry.json`.
- ZIP: `artifacts/releases/aapl-research-residual-v1.zip`.
- Sáu checkpoint LSTM residual last: h1/h5 × seeds42/123/456. Ba CNN h1 gốc để so sánh; persistence không có weights.
- Hai scaler tương ứng với LSTM residual và CNN absolute; snapshotvalidatedAAPL2015–2025, source Python, lock môi trường và verifier.73payloadfiles cộngmanifest/registry/README. Không bao gồm toàn bộ rawdata, preparedarrays, logs nghiên cứu hoặc môi trường ảo.

Manifest chốt đường dẫn tương đối, hashes, representation và scalerID theo từngmodel. Không chọn checkpoint mới nhất trên đĩa. Source checkpoints giữ nguyên purpose/metadata gốc; manifest release ghi nhận việc nghiệm thu và liên kết, không sửa metadata lịch sử.

## Python interface để tích hợp ở mục8

```python
from backend.inference.release_forecaster import ReleaseForecaster

engine = ReleaseForecaster(project_root, release_id="aapl-research-residual-v1")
rows = engine.predict(inputs, methods=["lstm", "persistence"], seed=42)
```

`inputs` là list ForecastInput đúng bảy trường của TV2: sample_id, dataset_version, forecast_origin, input_dates, input_values, lookback, forecast_length. Inputvalues rawUSD30×1; không có target/actual/scaler/checkpoint path. Batch không được trùngID hoặc trộn version/mode/lookback. Snapshot là nguồn kiểm lịch/giá; model chỉ nhận tensor lịch sử input, không nhận actual tương lai.

Seed mặc định42 đã chốt, hỗ trợ42/123/456 nguyên. H1 methods lstm/cnn/persistence; H5 chỉlstm/persistence. CPUfloat64, một thread. Không fit/optimizer/train trong inference.

- LSTM: relativeX=(history−origin)/scale_train, outputdelta được decode giá=origin+scale_train×delta. Không cộng scalermean vào delta.
- CNN: absoluteStandardScaler→CNN→inverseabsoluteprice.
- Persistence: lặp giá cuối cùng của input choHphiên.

Mỗirow có releaseID/SHA, datasetversion, sampleID, method, seed/run/modelversion hoặcbaselineversion, scaler/representation, origin, forecastlength, horizonstep, targetdate, predictedpriceUSD, result_source vàscope. Không có actual/error tự ghép. H5 làdirect5output, khôngrecursive. Service/API sau này chịu validate request theo ngày, xây input hợp lệ và ghépcomparison riêng nếu cần; không truyền target vào engine.

## Phạm vi lịch sử và lỗi từ chối

Target chỉ thuộcvalidation2023 hoặctest2024–2025 trong snapshot đã khóa. Input có thể chứa lịch sử trước đó. Mọi target của h5 phải cùngsplit; crossing2023→2024 bị từ chối, crossing2024→2025 được phép vì đều test. Không suy ngày giao dịch bằng cộng calendar day, không live/tương lai ngoài snapshot, không cho client chọn arbitraryfiles.

Release kiểm registry/manifest/hashes và liên kếtmodel/scaler trước mỗi request. Chặn input cótarget, sai giá/ngày/version/ID, seed/method/horizon sai, artifact thayđổi và scaler không khớp. Code/model đãpin nếu thay đổi phải tạo phiên bản release mới; không cập nhật hash chỉ để bỏ qua lỗiintegrity. Hashes là kiểm toàn vẹn cục bộ, không là chữ ký xác thực nguồn bên ngoài.

## Chạy trực tiếp hoặc từ ZIP

Trong workspace đã có môi trường được nghiệm thu:

```powershell
.venv/tv4_clean/Scripts/python.exe scripts/verify_tv6_release.py
```

Khi nhận ZIP, giải nén vào thư mục riêng. Dùng Windows64-bit/CPython3.13.7 và dependencies theo `scripts/requirements-tv4-lock.txt`; sau đó chạy `python scripts/verify_tv6_release.py` từ nguồn giải nén. Verifier đọc snapshot, nạp đủ9model qua tất cả3seed và kiểm ngày/shape/finite/baseline. Không cần preparedarrays, downloadYahoo hoặc training.

Đã chạy ZIP giải nén trong tiến trình `python -I`, importsource từ thư mục riêng, dùng **cùng môi trường dependencies trên cùngmáy**. OutputSHA khớp workspace. Cài mới/máy thành viên khác chưa được xác nhận, không coi đây là bằng chứng đó. ZIP làgói inference, không phải toàn bộ hồ sơ nghiên cứu; audit/metric đầy đủ vẫn ởworkspace vànotebook.

Builder `scripts/build_tv6_release.py` không ghi đè release cũ; `--draft` tạo manifest nháp riêng để kiểm tra trước khi chốt. Các script không tạo/huấn luyện model.

## Giới hạn khoa học giữ nguyên

Giá adjusted hồi cứu, không là dữ liệu point-in-time. Residual được phát triển sau khi quan sát test cũ; lợi thế baseline nhỏ, không là chứng minh độc lập hoặc lợi nhuận giao dịch. `independent_holdout=false` được giữ trong metadata/output. Nghiệm thu mục7 xác nhận tích hợp và tái lập inference, không nâng cấp kết luận hiệu năng mô hình.

Xem [báo cáo nghiệm thu](../reports/audits/TV6_Item7_Release_Integration.md). API/frontend và kiểm chứng máy khác còn các hạng mục tiếp theo.
