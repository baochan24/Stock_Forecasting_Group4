# TV6 mục8 — API lịch sử và cách chạy

Hoàn thành local27/11/2026, FastAPI0.165.0/Uvicorn0.54.0, Python3.13.7/CPU. API dùngrelease `aapl-research-residual-v1` đãnghiệmthu, khôngtrain/modelmới hoặcgiao diện. [Báo cáo kiểm chứng](../reports/audits/TV6_Item8_API.md).

## Chạy trongworkspace

Sau khi cập nhật source, dừng tiến trình API cũ bằng Ctrl+C, chạy lại script và tải lại `/docs`. Server không bật auto-reload. Swagger có mẫu hợp lệ cho predictions (`2023-06-15`, h1) và model-traces (cùng ngày, h5); `/forecast-origins` trả danh sách ngày hợp lệ. Không dùng chuỗi `string` làm ngày.

Tái audit mới nhất: 51 tests và 15 kiểm tra HTTP đạt; notebook lưu output kiểm toàn bộ 20.144 dòng cùng 12 nhóm metric. Metric từ chối keys trùng/thiếu và actual không khớp giữa các phương pháp. Chi tiết và giới hạn trong báo cáo nghiệm thu.

Môi trường `.venv/tv4_clean` hiện đã có dependencies API;69package theoTV4corelock vẫn khớp. Cài ở môi trường phù hợp bằng lock, không tựchọn bản mới:

```powershell
.venv/tv4_clean/Scripts/python.exe -m pip install -r scripts/requirements-tv6-api-lock.txt
.venv/tv4_clean/Scripts/python.exe scripts/build_tv6_api_data.py
.venv/tv4_clean/Scripts/python.exe scripts/run_tv6_api.py
```

Swagger: `http://127.0.0.1:8000/docs`, schema: `/openapi.json`. Scriptchỉ bind127.0.0.1,mộtworker,port mặcđịnh8000; có `--port 8001`. Không cầntrain hoặcdownloadYahoo. Server nghiệmthu tạm đãdừng sau kiểm tra; lệnh trên khởi chạy phiên sửdụng của người dùng.

Nguồn vàartifact cầnđúngbộ: release mục7 + sidecarAPI `artifacts/releases/aapl-research-residual-v1-api-data/` vàregistry `experiments/configs/tv6_api_data_v1.registry.json`. Sidecar chứa20.144storedpredictionrows đãđối chiếu vàhistory/config của9experiment. Builder chỉ đọc dữ liệu đã nghiệmthu, khôngforward/train, khôngghiđè artifact sai hash. ZIPmục7 làgói inference đãkhóa, chưa chứaAPI/sidecar mới; bàn giao đầyđủ tiếp tục mục10.

## Endpoints /api/v1

| Method | Endpoint | Nội dung |
|---|---|---|
| GET | `/health` | Process sống; không đòi artifacts |
| GET | `/readiness` | Kiểm release/resultshashes; coldwarm đủ9model;503 nếu khôngsẵn sàng |
| GET | `/releases/current` | Releasehiện tại, capabilities,9experimentIDs,giới hạn |
| GET | `/releases/{release_id}` | Thôngtinrelease,404 nếu khôngcó |
| GET | `/forecast-origins` | Origin hợp lệtheo1/5bước vàrange/phântrang |
| GET | `/datasets/{dataset_version}/prices` | GiáadjustedUSD lịch sử,range/phântrang |
| POST | `/predictions` | Inference input-only, comparison riêng |
| GET | `/results` | Đọcstoredresults, khôngforward |
| GET | `/metrics` | Tính bằngEvaluation từstoredresults cùngcohort |
| GET | `/experiments/{run_id}` | Metadata/config côngkhai vàhistoryarchived cóphântrang |
| GET | `/experiments/{run_id}/audits` | AuditID/hash/checks củarelease cómodel đó |
| POST | `/model-traces` | TraceLSTM táitính/đối chiếu sốhọc,summary/full |

Khôngcóendpointtrain/fit/live/tickerkhác. Khôngupload hoặcclientchọn checkpoint/scalerpath. APIgiữ kếtluận khoa học trongmetadata; chấtlượngAPI không tựtăng độchínhxác hoặc tínhđộclập của model.

## Request dự báo

```json
{
  "release_id": "aapl-research-residual-v1",
  "forecast_origin": "2023-06-15",
  "forecast_length": 5,
  "methods": ["lstm", "persistence"],
  "seed": 42
}
```

releaseID mặcđịnh làreleaseđãchốt, seed42mặcđịnh; chỉ42/123/456nguyên. Forecastlength1/5nguyên; h1choLSTM/CNN/persistence,h5chỉLSTM/persistence, methodsduynhất. DatephảiYYYY-MM-DD vàphiênsnapshot hợp lệ, đủ30input/targetcùngsplit validation2023 hoặctest2024–2025. H5cross2023→2024bịchặn;2024→2025được phép nếuđủphiênvìcùngtest. Không nhậninputraw/actual/target từclient: server xâydựngForecastInput theo release.

Response córequest_id (khớpheaderX-Request-ID),releaseID/SHA,datasetversion,status,result_source,inputcontext,methodsstatus,predictions vàcomparison. `predictions` khôngcóactual/error; `comparison` đượcghép sauinference. Không cópartial âmthầm: nếu thiếumethod/horizon thì503, khôngbáocomplete. Phươngpháp/runtimeerror trảfailed thay vìtínhso sánh trênnhóm cònlại.

## Query và phântrang

- Origins: `forecast_length`, `origin_from`, `origin_to`, `release_id`, `offset`, `limit`. Defaultlimit100,max1000,offset0..100000. Tổng752originsh1 và744h5 hiện tại.
- Prices: `start_date`, `end_date`, `release_id`,offset,limit. Default500,max3000.
- Results/metrics: `forecast_length`, `seed`, `methods` lặpquerykey (ví dụ `methods=lstm&methods=persistence`),`split=val|test`,originrange,releaseID,offset,limit. Defaulttest,h1,seed42,LSTM/persistence. Dates lọc theo **forecast_origin**, khôngtargetdate.
- Experimentshistory: offset,limit (default100,max1000). RunID phải nằmtrongallowlist9model, khôngdùng làm arbitraryfilepath.

Extraquery/bodyfields bịtừchối ở cácschema đãđịnhnghĩa; limit/range/mode/method sai422. Results pagination chỉ phântrangoutput, metrics luôn tính đủcácmẫu đượcchọn trước khi phântrangdòngmetric. Mẫu rỗng/khôngcùngcohort giữa cácmethod trả422, khônglấyintersection đểchethiếu.

Metrics là **seed đượcchọn** (default42),khôngtựđổi thànhmean3seed nghiêncứu. H5trảtừnghorizonvàoverall; sample_countN/error_countN×5 đượcphânbiệt. `range_kind=selected_range` khi cóoriginfilter, còn `release_full_split` nếuđủsplit. Cảhai không phải testđộclập mới. `evaluation_phase` giữvalidation_used_for_selection,post_development_old_test hoặcoriginal_locked_test theo nguồnmodel. Không trộnmodel/scaler hoặcrelease.

## Trace và lỗi

Tracebody gồmreleaseID,forecastorigin,length,seed và `detail=summary|full` (defaultsummary). ChỉLSTM, mộtwindow30phiên,hidden32,h1/h5. Summary trảmean từnggate/h/c mỗi bước;full trảvector32units. Các trườngscaledtrongtraceTV3 làtọa độdelta/relative của residual, không phải giáUSD; `predicted_prices_usd` làdecodeđúng. Trace chỉtrảkhi táitínhgate/h/c/output khớpnn.LSTM vàforward, không cậpnhậtweights hoặcoptimizer.

Lỗi chung: `{request_id,status:'failed',error:{code,message,details}}`.404unknownrelease/dataset/run;422schema/origin/range;503artifacts/results/inference/tracekhôngsẵn sàng;500ngoàidựkiến. Traceback/path nội bộ chỉ ở `logs/api/requests.log`; client không nhận. Requestlogs cómethod/path/status/duration vàrequestID, không logtargetđểmodelhọc.

CORS mặcđịnh chỉlocalhost/127.0.0.1:5173, khôngcredentials. Cóthểchốt origins khác qua `TV6_CORS_ORIGINS`; frontendframework chưa chọn ởmục8. APIđượckiểm vớithread-safe serialized CPUinference, mộtTorchthread; chưa là loadtest hoặcdeploymentInternet.

## Tái kiểm

```powershell
.venv/tv4_clean/Scripts/python.exe -m pytest tests/api/test_tv6_api.py -q -p no:cacheprovider
.venv/tv4_clean/Scripts/python.exe scripts/check_tv6_api_http.py
```

HTTPchecker khởichạy server riêng trên127.0.0.1porttạm và tựdừng saukiểm tra. Đãđạt46tests và15HTTPchecks. TestClienttheo [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), queryschemas theo [Query parameter models](https://fastapi.tiangolo.com/tutorial/query-param-models/), lỗi tùychỉnh theo [Handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/). Pins thực tế trongrequirementsAPI; pipcheck đạt. Haiwarningdeprecation từanyio/Starlette đượcghi log, khôngtestfailure; không nângcorelibs chỉđểchewarning.

Notebook06 có46cells/23code cells vớioutputAPI/metric/verifiedgateplot. Chưa xácnhận máy khác; frontend làmục9, finalhandoff làmục10.
