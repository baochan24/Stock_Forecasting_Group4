# Decision log

## 27/11/2026 — TV6 mục9 frontend theo concept đã duyệt

Người dùng giao triển khai mục9, giữ giao diện đã chốt. Dùng HTML/CSS/ES modules không dependency npm, SVG/table từ API, proxy localhost5173 tới API8000. Giữ nền sáng/sidebar/biểu đồ trung tâm/thẻ mô hình/nhật ký; bổ sung màn dữ liệu, metric full/range, stored errors, history/audit và trace verified đúng trách nhiệm TV6. H5 tự bỏ CNN, không target vào inference; không train/fit/tính MAE/RMSE phía frontend. Nguồn/snapshot/giới hạn hồi cứu và test cũ sau phát triển phải hiển thị; nhật ký chỉ bộ nhớ tab. Không mở live/trading/deployment Internet, không thay model/release hoặc tự hoàn thành mục10. Xem docs/TV6_Frontend_Demo.md và reports/audits/TV6_Item9_Frontend.md cho bằng chứng thực thi.

## 27/11/2026 — TV6 mục8 API

Người dùng giao mục8: chọnFastAPI/Uvicorn, APIcontract /api/v1 đủ12route,seed42default/h1-h5/baselines/readonlyresults/metrics/trace/health/readiness. CàiAPIdepsvớiconstraintsTV4,69corepinsgiữnguyên,lockAPIriêng; khôngtrain/model/frontend hoặcđổi releasev1 đãpin. Sidecarresults lưu riêngvàghimreleaseSHA/hash.46tests/15HTTPchecks thật đạt; serverkiểmnghiệm tựdừng. Clientkhôngtarget/path/scaler, error/requestIDsanitized,CORSlocal,tracecóđốichiếu. BáocáoTV6_Item8_API.md, setupTV6_API_Setup_and_Contract.md; notebook46cells/23executedcode. Chưa hostInternet/xácnhậnmáykhác; tiếp theo mục9.

## 27/11/2026 — TV6 mục7 release và tích hợp

Theo yêu cầu “tiến hành” mục7, tạo release nghiên cứu lịch sử aapl-research-residual-v1,6LSTMresidual/3CNNh1/persistence, defaultseed42, khôngtrain hoặc thayweights. Registry ghim manifest/artifacts/source, encoder/decoder vàscaler theo từngmodel. Runtime input-only, historical2023–2025, h5cùngsplit, khôngAPI/live/train.14tests vàE2E20.144predictionrows khớpacceptedoutputs; ZIP giảinén/nguồn riêng trêncùngmáy cho cùngoutputdigest. Khôngcoi là máy khác hoặc nâng kếtluận hiệu năng. BáocáoTV6_Item7_Release_Integration.md, contractTV6_Release_Contract.md; notebook42cells/21executedcode. Tiếp theo mục8API khi đượcgiao, chưa tự triển khai.

## 27/11/2026 — hoàn tất chốt ứng viên, không train thêm

Người dùng yêu cầu hoàn thành hạng mục sau giới hạn không train/model mới. Giữ residual last h1/h5 đủ3seed vàkhóa sáucheckpoint/scaler trongtv6_lstm_residual_candidate_v1.json trước đánhgiá. Cho đánhgiá ứngviên trên testcũ một lần theo protocol riêng ghi rõpost-development/khôngđộc lập, không tuning/chọnseed sau kếtquả. Không sửa protocol/catalogv1 hoặc đưavàoAPI/demo.18pipelinechecks vàaudit độc lập đạt; MAE residualtestcũ2,465892(h1),4,607636(h5overall), persistence2,476989/4,632497; lợi thế nhỏ vàkhông là bằngchứngđộc lập. Notebook38cells/19executedcode, báo cáoTV6_LSTM_Candidate_Completion.md. Dừng train/tuning, bàn giao ứngviên cho mục7 theoflow.

## 27/11/2026 — ablation một yếu tố, LSTM h1 mean readout

Người dùng yêu cầu tiếp tục sau hướng sửa có kiểm soát. Chọn thử một yếu tố: dùngmean30hidden thaylast hidden, cùng4513params, relativeinput/deltatarget/zerohead/scaler/cohort/sampler/lr/batch/maxepoch/patience/3seed.6runs mới trêndevelopment2022/2023; control tái sử dụng các last-readout run đãpin. Đánh giáaccuracy vàreal-vsflat/synthetic sensitivity, loggradient theoepoch. Không mởCNN/h5 trong ablation này, khôngtestforward hoặcpromote. Giữ cả kết quả xấu; tănggradient không tự là điều kiện chọn model. Plan tv6_mean_readout_ablation_v1.json, runCLIrun_tv6_readout_ablation.py.

Kết quả6/6run hoàn tất: meanreadout kém hơn ở2022, chỉ nhỉnh rất ít ở2023, không đáp ứng cải thiện nhất quán cả2fold. Không áp dụng meanreadout vào ứng viên hiện tại; giữ last residual, không sửa catalog/testv1. Hai tests vàaudit độc lập48metrics/12.024predictionrows đạt. Báo cáo TV6_Readout_Ablation.md; notebook34cells/17executedcode. Không mở thêm trial trong bước này.

## 27/11/2026 — xử lý ưu tiên1 sau phân tích LSTM

Người dùng yêu cầu “tiếp tục fix bước tiếp theo”. Bước này bổ sung tham chiếu meanchange chỉ tính từ train và phép đo gradient trên bản sao checkpoint/initialization, dùngdevelopment2022/2023 đủ3seed/h1/h5. Mục tiêu xác định giá trị học chuỗi và đường truyền gradient trước khi sửa tham số. Không optimizerstep, không thay checkpoint, không train mới hoặc testforward. Tham chiếu drift ởerror_analysis, không thêm vào release/baselineprotocolv1. Plan tv6_lstm_learning_check_v1.json; cập nhật notebook sau khi có kết quả thật.

Kết quảlocal:7tests/audit độc lập đạt;4reference/70metricrows/108gradientprobes. LSTM nhỉnh hơn train-meanchange nhưng mức lợi ích nhỏ, chưa quy được cho sử dụng lịch sử. Checkpointcore cógradientnonzero và đã đổiweights; gradientvịtrícũ nhỏ hơn vịtrígần khoảng1e-6–1e-7 trênbatchkiểm. Không có bằng chứng cần vá đứtbackprop. Báo cáo TV6_LSTM_Learning_Check.md; notebook30cells/15executedcode. Chưa trainablation hoặc promote model.

## 27/11/2026 — TV6 mục6, báo cáo trước khi sửa

Theo yêu cầu người dùng, hoàn thành erroranalysis/test v1 và12checkpoint residual LSTM history probes trêndevelopment2022/2023. Không train/updateweight/scaler, không testforward mới; giữ đủ3seed, dùng controls flat/reverse/shuffle chỉ để mô tả sensitivity, không chọncontrol theo điểm validation. Phát hiện residual h1fold2023 gần drift hằng số, v1 lỗi ngoại suy không chỉshock, lợi thế persistence nhỏ/không đều và chưa có độc lập sau phát triển. Báo cáo TV6_Item6_Error_Analysis.md cùngnotebook26cells cóoutput. Bước kế tiếp theo người dùng là xem báo cáo rồi sửa có kiểm chứng, chưa tự sangmục7.

## 27/11/2026 — cho phép thử nghiệm cải tiến residual sau test

Người dùng yêu cầu triển khai sửa và kiểm chứng cải thiện sau phân tích persistence gap. Thử nghiệm phiên bản origin-centered-price-delta-v1, relative history/delta target và zero output head, giữ core LSTM/CNN và float64. Đối chứng absolute-price cùng2fold validation2022/2023,3seed,36runs,max100epoch/patience10/lr0.001. Scaler fit lại đúng train mỗi fold; không refit scaler v1, không đọc test targets/forward test, không tự đưa checkpoint mới vào frozen catalog. Đây là phát triển sau test, không là kết quả held-out mới. Chi tiết docs/TV6_Residual_Development_v1.md và config tv6_residual_development_v1.json. Số liệu thực tế chỉ bổ sung sau chạy.

Kết quả local:36/36runs hoàn tất,10tests mới vàaudit độc lập đạt. MAE residual giảm21–42% so đối chứng mới trên6task/fold; so persistence lợi thế nhỏ và h5fold2022 còn kém. Giữ candidate dưới purpose development, chưa promote/release hoặc thay testv1. Báo cáo reports/audits/TV6_Residual_Development_Results.md; notebook06 có22cells/11executedcode. Control mới cùngsampler/mẫu vớiresidual, không phải tái lập điểmv1(common60/shuffleFalse).

## 26/11/2026 — TV6 mục3, input-only inference validation

Theo yêu cầu triển khai mục3 và kiểm liên tục, thêm FrozenForecaster dùng protocol/registry trước mỗi request, adapter TV3/scaler TV2 và model helpers hiện có. Giữ model/weights/config và lock v1. Cho validation2023 để nghiệm thu đường inference một/năm bước, chưa cho phép test hoặc bypass allow_test trước mục5. Release_id=None trước tích hợp release mục7. Không join actual/tính metrics trong engine, không fit/update weights.69 tests và full-validation9 models/2 baseline modes đạt; việc mở đường final test cần tích hợp/kiểm chứng sau evaluation mục4.

## 26/11/2026 — audit và siết guard protocol TV6 mục2

Theo yêu cầu audit/sửa các điểm khóa, giữ nguyên bytes/fingerprint protocol v1,9 model,cohorts502/498,metric/demo seed42. Thay assert bằng explicit validation, chặn path ra ngoài root/unpinned references, đối chiếu model manifest và coverage source dates. Bổ sung registry riêng ghim lock cũ và receipt có trước, đăng ký tường minh, không tự tái tạo lock đã mất khi có dấu vết lịch sử. Đây là sửa khả năng thực thi/kiểm chứng, không thay thiết kế thực nghiệm sau nhìn test. Không model inference/metric test trong audit; registry local không là chữ ký hoặc bảo đảm tuyệt đối không có external test exposure.

## 26/11/2026 — TV6 mục2, khóa protocol trước đánh giá test

Trong yêu cầu hoàn thành mục2, giữ9 checkpoint đã nghiệm thu và ba seeds42/123/456, lookback30, CPU float64. Agent áp dụng mặc định demo seed42 cố định cho cả3 nhóm neural để minh họa, không chọn seed tốt nhất theo validation/test và không gán đây là câu chọn seed trực tiếp của người dùng. Không tự chọn phương pháp thắng để làm default sản phẩm; demo hiển thị các phương pháp được hỗ trợ.

Protocol tv6-final-evaluation-v1 tại experiments/configs/tv6_evaluation_protocol_v1.json khóa data/scaler/checkpoints/config/history và cohorts qua SHA256. Một bước502 samples so LSTM/CNN/persistence, năm bước498 so LSTM/persistence trên full target split2024–2025, cùng ordered IDs/ngày trong mỗi chế độ. Dự báo rolling theo lịch sử thực tế đã quan sát, weights/scaler cố định; h5 direct output, không recursive hoặc nạp target tương lai.

MAE/RMSE USD không làm tròn trước metric, báo h1–h5; h5 overall phụ là flatten tất cả sample-horizon errors, RMSE=sqrt(mean squared errors), không trung bình RMSE của5 horizon. Mean/std mẫu ddof1 trên metric từng seed, không pooling predictions thành ensemble; baseline deterministic không giả lập3 seeds. Numeric tie atol1e-12USD chỉ biểu thị dung sai số, không phải ngưỡng cải thiện thực tiễn hoặc ý nghĩa thống kê; MAE/RMSE trái chiều báo tradeoff, không tạo composite score. Chưa chốt practical-significance threshold, không tuyên bố ý nghĩa thống kê từ3 seeds/overlapping h5 windows.

Không tuning/train/refit/chọn seed/checkpoint bằng test. Drift artifact/cohort/policy làm protocol không hợp lệ, phải ghi phiên bản mới có lý do; không âm thầm ghi đè lock. Mục2 chỉ tạo/kiểm protocol, chưa chạy inference/performance test hoặc frontend/API.

## 26/11/2026 — TV6, chốt nguyên tắc concept frontend để triển khai sau

Người dùng chấp thuận ảnh concept AAPL Forecast Lab và yêu cầu giữ nguyên tắc khi đến hạng mục frontend. Đây là định hướng giao diện, chưa cho phép triển khai ngay hoặc tự động mở rộng nguồn dữ liệu/thay contract nghiên cứu.

- Giao diện nền sáng, sidebar điều hướng, biểu đồ lịch sử/vùng dự báo ở trung tâm, thẻ LSTM/CNN/persistence và nhật ký dự báo. Hiển thị release, nguồn và thời điểm dữ liệu.
- Tách chế độ nghiên cứu lịch sử dùng snapshot/release khóa với khả năng theo dõi phiên mới. Dữ liệu thị trường thực chỉ tích hợp sau khi chốt nguồn/quyền sử dụng và data contract; không gắn nhãn real-time khi chưa xác minh. Không ghi đè snapshot/scaler/model nghiên cứu.
- Một bước chỉ hiển thị T+1. Năm bước chỉ hỗ trợ LSTM/persistence, không CNN. Theo phiên dataset, không cộng ngày lịch.
- Model dùng 30 phiên adjusted close đã hoàn tất, không tự dùng giá intraday thay giá đóng cửa. Giá thị trường và adjusted close phải có nhãn đúng ngữ nghĩa.
- Inference không nhận target, không train/refit scaler từ giao diện. Actual được ghép sau để đối chiếu; chưa có actual phải thể hiện đang chờ.
- Metric chính thức toàn tập tách metric khoảng chọn và theo dõi mới. Không coi biểu đồ bám giá là bằng chứng vượt baseline. Trace minh họa tách trace đã kiểm chứng.
- Ảnh concept chứa số liệu minh họa, chưa kết nối thị trường. Những sai lệch hình minh họa (đường T+1…T+5 khi chọn một bước, CNN nhiều bước) không phải yêu cầu triển khai.

Ảnh tham chiếu lưu tại reports/figures/ui_concepts/TV6_AAPL_Forecast_Lab_Concept_v1.png. Chỉ dùng làm tham chiếu khi đến frontend, chưa chốt framework/API/deployment. Không triển khai frontend, lấy dữ liệu mới hoặc push Git trong tác vụ lưu quyết định này.

## 26/11/2026 — TV5 mục9, phạm vi so sánh validation

Theo yêu cầu thực hiện mục9, dùng 250 mẫu validation2023 chung cho CNN/LSTM lookback30/persistence. Giữ ba seed, không tuning hoặc chọn seed theo kết quả. Bổ sung tối thiểu persistence input-only và one-step MAE/RMSE dùng chung ở module TV6 vì workspace chưa có implementation; không triển khai API/release hoặc nghiệm thu toàn bộ TV6. Đánh giá test2024–2025 cuối vẫn thuộc flow TV6 sau khóa đầy đủ protocol. Báo giới hạn validation selection và ngân sách tìm kiếm khác nhau của CNN/LSTM.

## 26/11/2026 — TV5 mục 8, khóa và chạy phương án A

Theo yêu cầu chạy mục 8, giữ nguyên cấu hình đã chốt trước smoke. Lock semantic config data/model/training/seeds/runtime trong cnn_one_step_option_a.lock.json, baseline YAML có SHA256 và semantic fingerprint. Official entry point từ chối drift kiến trúc/ngân sách/seeds/runtime trước run. Output paths có thể đổi để tạo artifacts mới. Ba seed 42/123/456, max100/patience10, trần300, best validation từng seed, báo mean/std ddof1 và giữ cả ba checkpoint. Không chọn seed theo test hoặc sửa tham số dựa vào smoke. Purpose research cho official runs; smoke vẫn diagnostic.

## 26/11/2026 — TV5 mục 6, checkpoint CNN

Theo yêu cầu thực hiện mục 6, nối saver CNN riêng vào runner chung. Giữ CPU float64 và schema dữ liệu một bước. Artifact chứa weights/config/provenance/run/seed/best validation và fingerprint training config. Loader yêu cầu expected identity/config từ nguồn tin cậy, mặc định từ chối diagnostic kể cả đã train tổng hợp. Runner nhận checkpoint_purpose research/diagnostic, smoke mục 7 dùng diagnostic. Đây là best-model/inference persistence, không phải resume optimizer. Metadata do caller cấp không tự chứng minh train thật; tiếp tục kiểm logs ở các mục sau. Không đổi kiến trúc/ngân sách phương án A.

## 26/11/2026 — TV5 mục 2, contract và precision

Theo yêu cầu hoàn thành mục 2 sau khi chốt phương án A, giữ kiến trúc CNN tác giả, 17.057 tham số, lookback 30, một feature và một output. Chọn CPU float64 cho model và input để đồng nhất precision với pipeline LSTM/TV2 hiện tại. Đây là lựa chọn triển khai được agent áp dụng trong phạm vi mục 2, dựa trên đề xuất đã trình bày; không gán thành yêu cầu đề gốc hoặc tuyên bố float64 dự báo tốt hơn.

Conv1d và Linear khởi tạo float64 tường minh, không thay global torch dtype hay tự cast input. Config khóa hợp đồng một bước, kiểm kiểu/số dương và dropout hữu hạn. Forward kiểm CPU, dtype, shape, batch không rỗng và số hữu hạn. Kiến trúc/seed/ngân sách A giữ như quyết định trước. Dữ liệu thật, Adam/dropout/reload và benchmark được nghiệm thu theo mục 3–7.

## 26/11/2026 — TV5 chọn phương án A

Người dùng chốt phương án A sau đối chiếu đề và sơ khảo ngân sách. Giữ một cấu hình CNN tác giả để so sánh với LSTM, hai Conv1d 1→16→32, kernel 3, MaxPool2, Dropout 0,1, Linear 480→32→1, tổng 17.057 tham số. Lookback 30, một feature và một output. Không mở rộng lưới kiến trúc B/C trong kế hoạch này.

Ba seed 42/123/456, tối đa 100 epoch/run, patience 10, Adam 0,001, batch 32 và MSE. Tổng ba run chính thức, trần 300 epoch. Dùng cùng 1.954 mẫu train và 250 validation với LSTM lookback 30, cùng scaler và quy tắc chọn best bằng validation. Ghi ngân sách smoke, tests, reload và thời gian CPU riêng. Báo đủ ba seed và std mẫu ddof=1, công bố khác biệt ngân sách LSTM/CNN.

Dtype CNN còn cần ghi thành quyết định riêng trong mục 2. Source tiếp nhận hiện mặc định float32; đề xuất float64 để đồng nhất điều kiện với LSTM chưa được coi là xác nhận của người dùng.

## 25/11/2026 - TV4 item 7

User authorized completing all pretraining audit items. Support lookback 10/30/60 using new immutable artifacts and common target dates with 60-session history. Plan 9 one-step runs plus 3 five-step runs at lookback 30, seeds 42/123/456, max 100 epochs and patience 10, one CPU thread. Total cap 1200 epochs. Select lookback by mean validation MSE across seeds, exact ties prefer shorter history. Report sample standard deviation ddof=1. One-epoch probes verify integration.

## 25/11/2026 — TV4 mục2 CPU float64

Theo yêu cầu tiếp tục mục2, đồng bộ loop với dtype64 TV3 đã được người dùng chọn; không đổi lựa chọn precision hoặc kiến trúc. Bỏ castfloat32, không tự migrate/cast model, kiểm CPU/dtype/shape/horizon và output khớp target. Loop chung giữ dtype generic model, chưa chốt CNN.52/52 tests và6/6 notebook cells đạt trên tensors tổng hợp, không AAPL/persistence thật; model/data/scaler TV1–TV3 giữ nguyên. Evidence tại reports/audits/TV4_Progress.md, tiếp theo mục3.

## 25/11/2026 — TV4 mục1 tiếp nhận source và sửa layout

Theo người dùng, hoàn thiện TV4 trước TV5, từng mục kèm logs/notebook. Nhận9 file PR#10 commit16555929210314b1eb06da9dc84b827ececc1b9e nguyên nội dung, đặt runner dưới backend/experiments/runner để khớp project/tests. Venv TV4 riêng có PyYAML, không sửa venv/source/data TV1–TV3. Mục1 chỉ nghiệm thu layout/import/baseline; castfloat32, placeholder dataset versions và checkpoint hook là phần chưa hoàn thành ở mục2/3/5. Không train AAPL, merge/push hoặc triển khai CNN trong mục1. Xem reports/audits/TV4_Progress.md.

## 23/11/2026 — dọn bản upload TV3 dư theo yêu cầu người dùng

Xóa 9 file trong ba package ở gốc nhánh Thiên: `lstm_one_step/`, `lstm_multi_step/`, `model_trace/`. Source hiện hành vẫn ở `backend/models/` và `backend/model_trace/`; không đổi interface/float64/phạm vi mô hình. Đã kiểm tra imports và chạy lại 99/99 tests sau khi xóa. Giữ lịch sử Git, các module phụ thuộc và khung TV4–TV6. Chi tiết: `reports/audits/TV3_Branch_Cleanup.md`.

## 23/11/2026 — TV3 mục6 chuẩn bị/verify bàn giao

- Theo yêu cầu người dùng tiếp tục mục cuối và lưu báo cáo/notebook: chốt docs consumer TV4/TV6 và checkpoint persistence contract, không triển khai training/selection/API thay thành viên. Giữ CPU float64; diagnostic trained=False bị từ chối mặc định, không gắn nhãn model khởi tạo là model nghiên cứu.
- Source/contract ZIP có checksum, trained_checkpoints=[];99/99 tests, integration5460 samples và trace6 stages đạt sau giải nén bằng venv sạch. Notebook mục6 gọi kiểm manifest/checksum/receipt đúng gói; source cells hash độc lập outputs để Run All không làm sai integrity.
- Báo cáo TV3_Final_Handoff.md/TV3_Progress.md ghi gói cuối/evidence/giới hạn. Chỉ đạt kỹ thuật local, máy người nhận/checkpoint train thật/API approval còn chờ; không upload/push/merge hoặc tự nhắn thành viên khác.

## 23/11/2026 — TV3 mục5 môi trường CPU sạch và notebook

- Người dùng yêu cầu tiếp tục mục kế và luôn ghi báo cáo. Tạo lock68 dependencies, tv3_clean không system/user packages; không thay mô hình/dtype/split hoặc venv TV1/TV2.
- Strict runner89/89 đạt, pip-check/versions/origins/CPU build đạt; bản source độc lập chạy tests/integration5460 samples/trace6 stages đạt, hashes nguyên. Notebook03 cập nhật mục5 và chạy12/12 code bằng kernel sạch, đã đăng ký kernel VS Code riêng.
- Báo cáo tiến độ và evidence tại TV3_Progress.md/TV3_Environment_Reproduce.md, setup docs/TV3_Setup_and_Reproduce.md. Chỉ nghiệm thu local, máy khác vẫn chờ; mục6 bàn giao chưa làm. Không train/tuning/metric/push/merge/Drive.

## 23/11/2026 — TV3 mục4 trace và notebook

- Theo yêu cầu tiếp tục mục kế và luôn cập nhật notebook, nghiệm thu trace sau update/reload/JSON cho hai mode. Tăng độ chặt float64 rtol1e-10/atol1e-12 phù hợp precision64 đã chọn; fallback32 giữ1e-5/1e-6. Không thay core fields/API hoặc công thức, docs/TV3_Trace_Contract.md vẫn là schema nội bộ chưa được TV6 duyệt.
- 89/89 tests và6 stage checks input TV2 thật đạt; update synthetic không training AAPL. Bổ sung mục4 notebook03, cells gọi CLI/source thực và trình bày gates/recurrence/sai số;4 đạt local,5/6 chờ. Evidence tại TV3_Progress.md. Không push/merge/Drive hoặc thay artifacts cũ.

## 23/11/2026 — notebook ghi quá trình từng phần TV

- Người dùng yêu cầu mỗi phần có notebook/cells để tìm hiểu, kiểm định và trình bày giảng viên. Tạo notebook TV2/TV3 đúng notebooks/, giữ EDA TV1; TV3 chỉ ghi nghiệm thu đến mục3,4–6 chờ. TV4–TV6 thêm khi bắt đầu.
- Builder/execute trong scripts, notebook gọi source/tests thật và lưu outputs/evidence; không tạo pipeline song song, không train hoặc thay đổi artifacts đã chốt. Thêm notebook tools vào venv TV3 riêng, không sửa TV1/tv2_clean; chưa coi là nghiệm thu môi trường sạch.
- Bổ sung vào rule yêu cầu cập nhật đúng notebook sau mỗi mục; không tự upload/push hoặc thay ZIP TV2 cũ. Chi tiết thao tác tại notebooks/README.md.

## 23/11/2026 — TV3 mục3 nghiệm thu model float64

- Theo yêu cầu tiếp tục mục3, bổ sung11 acceptance tests, không đổi model/adapter/contract. Suite77/77 đạt; nghiệm thu kiến trúc/forward/state/gradient/weight update và lưu/nạp sau một bước Adam tổng hợp. Gradcheck dùng tiny shared forward, tests default model riêng; không chứng nhận hội tụ/accuracy/training loop.
- Evidence và giới hạn tại reports/audits/TV3_Progress.md mục3. Giữ dtype64 theo lựa chọn người dùng, không tạo checkpoint nghiên cứu hoặc metric từ test; chưa push/merge/Drive. Tiếp theo mục4 trace; môi trường sạch và bàn giao còn mục5/6.

## 23/11/2026 — người dùng chọn thử giữ float64 xuyên suốt TV3

- Người quyết định: người dùng đề nghị giữ float64 để tránh hạ precision, sau đó yêu cầu triển khai thử. Thay lựa chọn float32 adapter trước bằng float64 cho adapter/model, không đổi kiến trúc/shape/split/scaler. Torch LSTM/Linear khởi tạo dtype64 explicit, không set global default; tests và CLI đồng bộ. Dung sai copy=0, inverse giá float64 rtol=atol1e-12.
- 66/66 tests đạt,5460 mẫu thật đạt; không sửa TV2 artifacts hoặc tính metric dự báo. Benchmark synthetic CPU batch32 1thread đo Adam step64 gần3 lần32, numeric weights/input storage gấp2; không suy rằng64 dự báo tốt hơn. Logs và số đo tại TV3_Progress.md phần precision. Trace/state_dict64 đạt.
- Giữ float64 làm cấu hình local hiện tại theo lựa chọn người dùng; TV4 phải ghi dtype trong training/checkpoint configuration. Chưa có checkpoint chính thức cần migrate, chưa train/tuning/test-selection/push/merge. Các mục3–6 không tự coi hoàn thành.

## 23/11/2026 — TV3 mục2, ranh giới tensor TV2→model

- Theo yêu cầu người dùng, thêm adapter trong preparation chuyển batch TV2 float64 sang CPU float32 đúng dtype model hiện có, không đổi artifact/shape/feature hoặc kiến trúc. Chọn dung sai kiểm cast standardized rtol1e-6/atol1e-7 và kiểm rawUSD sau cast rtol1e-6/atol1e-4; không thay tolerance float64 của TV2.
- Thay fixture preprocessing PR cũ bằng output module TV2;63/63 tests và toàn bộ5460 mẫu thật forward đạt, evidence tại TV3_Progress.md. Không training/metric/chọn model bằng test, không refit/scaler hoặc push/merge. Môi trường sạch còn mục5; bước tiếp theo mục3.

## 23/11/2026 — tiếp nhận TV3 mục 1 đúng module

- Người dùng yêu cầu bắt đầu xử lý hạng mục đầu tiên TV3 sau audit. Tiếp nhận10 file Python nguyên nội dung từ nhánh Thiện commit1f209b70c5690fb5e41b3b26d8eab36b2b6c029d vào backend/models, backend/model_trace và tests/models đúng contract. Không move/delete file sẵn có hoặc sửa remote; không đổi Define/Design.
- Chạy workspace thực55/55 tests đạt, logs và giới hạn môi trường tại reports/audits/TV3_Progress.md. Chỉ nghiệm thu mục1; tích hợp TV2, model/trace acceptance và bàn giao còn theo flow mục2–6. Chưa training/push/merge/Drive.

## 22/11/2026 — TV2 đóng gói preprocessing và kiểm chứng sạch local

- Theo yêu cầu người dùng hoàn thiện mục cuối TV2: giữ contract1/5 bước, lưu prepared NPZ không pickle và JSON records riêng, manifest/source hashes; không đổi mô hình/phạm vi/shape.
- Ghim dependencies tại scripts/requirements-tv2-lock.txt; tạo venv TV2 sạch riêng, không sửa môi trường TV1. Package/verify source+TV1 artifacts+scaler+prepared, không upload/push.
- 51/51 tests đạt trong workspace và bản ZIP giải nén độc lập; rebuild arrays exact. Chi tiết evidence tại reports/audits/TV2_Final_Handoff.md. Nghiệm thu liên máy vẫn chờ người nhận xác nhận thực; không tự ghi hoàn thành thay họ.

## 21/11/2026 — đối chiếu trực tiếp hai tài liệu đề gốc

- Theo yêu cầu người dùng, đã đọc `docs/đề_yêu_cầu.md` và `docs/yêu_cầu_mẫu_đề_tài.md` sau khi lưu nội dung (trước đó cả hai rỗng).
- Xác nhận hướng Topic 4 regression/LSTM/Yahoo Finance/next-day và hai mở rộng multi-step, CNN vs. LSTM phù hợp thiết kế hiện tại; không thay phạm vi/contract/flow TV2.
- Cập nhật rule.md đưa hai nguồn vào danh sách đọc bắt buộc; bổ sung đối chiếu tại Project Description, tách yêu cầu đề gốc khỏi lựa chọn cụ thể của nhóm. Ghi còn mở về quyền sử dụng dữ liệu, phương án dự phòng và mốc kế hoạch; không tự công bố đã đáp ứng.
- Chỉ thay tài liệu, không chạy test thuật toán hoặc thay kết quả audit TV2. Tiến độ giữ ở mục 5 hoàn thành local, tiếp theo mục 6.

| ID | Quyết định | Trạng thái |
|---|---|---|
| D01 | AAPL adjusted close 2015–2025, CPU, PyTorch | Đã thống nhất |
| D02 | Train 2015–2022, validation 2023, test 2024–2025 | Đã thống nhất |
| D03 | LSTM direct price/persistence; CNN một bước lookback 30 | Đã thống nhất |
| D04 | LSTM direct multi-output 5, lookback 30, checkpoint riêng | Đã thống nhất |
| D05 | Web hoàn chỉnh; train riêng; release_id thay thuật ngữ demo toàn hệ thống | Đã thống nhất |
| D06 | Architecture/modules/data flow/API/risks/milestones | Đã thống nhất về thiết kế |
| D07 | LSTM học thay đổi giá | Tùy chọn sau phạm vi chính/mở rộng |

Thay đổi mới ghi: ngày, quyết định, lý do, ảnh hưởng, người quyết định và bằng chứng. Không tự ghi đạt khi chưa kiểm tra.

## 20/11/2026 — quy trình bám flow coursework tại workspace

- Người yêu cầu: người dùng trong phiên làm việc, yêu cầu setup rule.md để đọc cốt lõi trước code/quyết định, tránh lệch flow đồ án.
- Tạo `rule.md` tại gốc workspace, dựa trên Project Description, module boundaries, data contracts, phân công và quy tắc repo đã có; tạo `AGENTS.md` làm điểm chỉ dẫn coding agent đọc rule này.
- Ghi rõ tài liệu phải đọc, bất biến nghiên cứu, flow TV2 1–10, cách nghiệm thu và cập nhật local. Trạng thái chi tiết tiếp tục nằm trong báo cáo audit, không thay tài liệu thiết kế bằng log hội thoại.
- Không thay mục tiêu, mô hình, split hoặc contract; không tuyên bố đây là quyết định biểu quyết của toàn nhóm. Giữ nguyên rule của checkout lồng. Đây là thay đổi tài liệu, không chạy test thuật toán.

## 19/11/2026 — tiếp nhận TV1 và bố trí script EDA

- Theo yêu cầu người dùng trong phiên làm việc: lấy riêng source TV1 PR #5 vào workspace hiện tại để xử lý từng bước; chưa nghiệm thu và chưa merge/push GitHub.
- Nguồn: `huyenntt2110-crypto/Stock_Forecasting_Group4`, commit `08675d823bd2499df1508dc4b4cde8722d557629` (PR #5). Tiếp nhận downloader, validator, test và báo cáo dữ liệu; không lấy TV2.
- Chuyển hai script build/execute notebook từ `notebooks/` sang `scripts/` theo yêu cầu người dùng, phù hợp ranh giới entry point; cập nhật đường dẫn và `FILE_STRUCTURE.md`.
- Không thay đổi Define/Design hay hợp đồng dữ liệu. Snapshot EDA mới vẫn tách biệt snapshot TV1 chưa được bàn giao; các số liệu trong báo cáo TV1 là kết quả do tác giả báo cáo, chưa được xác nhận trên snapshot gốc ở workspace này.

## 19/11/2026 — TV1, tài liệu và tái lập

- Theo yêu cầu người dùng, hoàn thiện riêng TV1 và cập nhật notebook tại workspace trước khi upload bản sao Drive. Không merge/commit/push GitHub trong phiên này.
- Snapshot làm việc cố định `aapl_2015_2025_acq_20261119T141302002415Z`; gói raw và gói đầy đủ cùng các audit có hash/receipt riêng. Không nhận chúng là artifacts version cũ của tác giả PR.
- Ghim dependencies trực tiếp TV1 ở `notebooks/requirements-eda.txt`; hướng dẫn mới dùng venv sạch không kế thừa system/user site, thay cách cài phát triển ban đầu. Script execute nhận Python được chỉ định qua `TV1_NOTEBOOK_PYTHON` để kiểm chứng môi trường riêng, vẫn mặc định `.venv/eda` cho notebook hiện tại.
- Tái lập cục bộ trong workspace riêng ghi kết quả thực tế tại báo cáo hạng mục 10; chưa có xác nhận máy thành viên khác. Không đổi phạm vi AAPL/CPU/shape hay quy tắc thực nghiệm.


## 27/11/2026 ? TV6 m?c5: m? test theo protocol ?? kh?a

Ng??i d?ng y?u c?u ti?p t?c m?c5. Th?c thi test2024?2025 ??9 checkpoint/seeds, kh?ng tuning/ch?n seed. Ledger ghi tr??c forward, gi? nguy?n protocol v1. K?t qu? persistence t?t h?n model; gi? k?t qu? th?t, ph?n t?ch nguy?n nh?n ? m?c6. Chi ti?t reports/audits/TV6_Item5_Test_Evaluation.md.
