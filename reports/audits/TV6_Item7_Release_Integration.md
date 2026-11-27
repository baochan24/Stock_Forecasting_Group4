# TV6 mục7 — release, inference và nghiệm thu end-to-end

**Hoàn thành local ngày27/11/2026.** Đã tạo bộ release nạp được, có inference input-only và ZIP kiểm chứng nguồn riêng. Không train/tuning/thay trọng số, không tạo API hoặcgiao diện. API làmục8, frontend làmục9.

## Đầu ra

Release `aapl-research-residual-v1` gồm6LSTMresidual last(h1/h5×3seed),3CNNh1 gốc vàpersistence. Giữ CNN làđối chứng theo extension củađề, không mở model mới. Manifest/registry chốt model, scaler, snapshot, biểu diễn vàsourcehash. Defaultseed42 cố định, đủ3seed được giữ, không chọn theo test.

- Manifest: `artifacts/releases/aapl-research-residual-v1/manifest.json`.
- Registry: `experiments/configs/tv6_research_release_v1.registry.json`.
- ZIP: `artifacts/releases/aapl-research-residual-v1.zip`,791.355bytes.
- ZIP SHA256: `3597bf6c98a5620a0c9c0ecd033a1f52a8c4e29aa6d78f249078970d32ae5926`.
- Release semanticSHA: `a4b04a50c3e499b95407a5a8f9de379a40f6371bbb532cc01df90fdb2b5719a3`.

Code mới: `backend/artifacts/research_release.py`, `backend/inference/release_forecaster.py`; builder/verifier/E2E trongscripts. Không sửa FrozenForecaster/protocolv1 hoặc các checkpoint đã nghiệm thu. Formatweights của LSTM làstate_dict.pt, CNN làweights.pt; builder giữ đúng tên/vị trí nguồn thay vì đổi/move file.

## Đường inference đúng biểu diễn

ForecastInput rawUSD→kiểmcontract/snapshot/hashes→encoder từngmodel→CPU64model→decodeUSD. LSTMoutput làdelta: origin+scale×delta. CNNoutput làabsolute chuẩn hóa: inverseStandardScaler. Persistence dùnggiácuối. Không dùnginverseabsoluteprice nhầm choLSTMresidual, khôngfit/refit và khôngtruyềntarget vào model.

Output córeleaseID/SHA, dataset, model/seed hoặcbaselineversion, origin, horizon vàngàyphiênthật, USD vàscope. Không cóactual/error tronginference. Inputtarget dư, saiID/version/giá/lịch, seed/method khônghợp lệ, thiếu/nghịch artifact hoặcscaler bịnạp nhầm đều bịchặn trướcforward.

Chỉphục vụ lịch sửtarget2023–2025. H5 phải cùngsplit; không live2026 hoặc lịchfuture đoán thêm. Hướng dẫn [TV6_Release_Contract.md](../../docs/TV6_Release_Contract.md).

## Bằng chứng nghiệm thu

| Kiểm chứng | Kết quả |
|---|---|
| Bản nháp tích hợp | 14tests đạt trước khi chốt |
| Bản chính thức | Cùng14tests đạt,13,07giây |
| Full validation/test | 22nhóm method/mode/seed/split,20.144predictionrows |
| So accepted outputs | Maxabsdifference=0 cho tất cả nhóm |
| Khôngfit | fit/partialfit bịspy chặn khi chạyE2E, khôngoptimizer/training |
| ZIP tách nguồn | Giải nén, kiểmCRC/hash, chạyPython `-I`, importbackend từthưmụcriêng |
| Kiểm9model saugiảinén | Đủ3seed/h1/h5, outputSHA khớpworkspace |
| Notebook | 42cells/21code cells cóoutput thật, gồm livebackendinference ngàyvalidation vàsơđồ |

14tests có cả h1/h5positive/repeat/khôngmutate input, seed43/bool/string, inputtarget/price/date/version/lookback/duplicate, CNNh5/crosssplit, filehash thayđổi vàwrongscaler trongmanifest đượcfixture reseal. Không cộng trùng sốtest nháp/chínhthức thành28testkhácnhau.

E2E đối chiếuLSTM với kếtquả residual đãchốt, CNN với evidence gốc vàpersistence cùngkey. Giữbatchcuối, mọi model/seed được nạp lại, không lẫnLSTMv1 vào residual. Các request fullbatch246–502mẫu ghi nhận khoảng0,78–1,51giây trênmáy này; đây không làbenchmark production/single-user API hoặcpeakRAM.

## Gói portable và giới hạn

ZIP có73payloadfiles cộngmanifest/registry/README: weights/scalers/snapshot/backendsource/lock/verifier. Không cóvenv/git/secrets hoặc toànbộdatasetraw/prepared/lognghiêncứu. Đườngdẫn tươngđối trongmanifest, khôngphụ thuộc `D:\learn_DeepLearning\Project_course-work` khi chạy nguồn giảinén.

Nguồn riêng: `.venv/tv6_release_verify_20261127T031224457203Z`. Kếtquả workspace/giảinén đều cópredictionSHA `a2c3373d08ae7e5e849d88801ec0d7214fa7bd684e465415e002b15f5e4581c0`. Dùngcùnginterpreter/dependencyenv, không phải kiểmchứng máy thành viên khác hoặc cài mới từzero. Mục10 tiếp tục reproducibility/handoff thực tế.

Đóng gói chỉ bảo đảm phần mềm nạp đúng bộ vàtái lập inference. LSTMresidual vẫn có lợi thếbaseline nhỏ, đãphát triển sau khi xemtestcũ; không thêm tuyênbố độc lập, ýnghĩathốngkê hoặc lợi nhuận.

## Logs và trạng thái tiếp theo

- E2E: `logs/audit/tv6_item7_20261127T031206056552Z/summary.json`, checks.csv,release_predictions.csv,acceptance.json vànotebook_verification.json.
- JUnit chínhthức: `logs/audit/tv6_item7_release_final_tests.xml`.
- Portable: `logs/audit/tv6_release_portability_20261127T031224457203Z/summary.json`.
- Notebook06 đã cóbảngcatalog/outputmẫu/checklist vàsơđồ, builder đồngbộ; giữoutputcũ. Cellmục7 chạy inferencevalidation nếuRunAll, khôngtrain hoặctínhmetric mới.

Mục7 đạt phạm vi đãgiao. Bộ inference sẵn sàng để nối API ởmục8 theo hợpđồng đãthiếtkế. Chưa triển khaiendpoint/health/readiness hoặcfrontend; chưaupload/push. Khôngcần Docker hoặctrain lại để kiểmgói cục bộ này.
