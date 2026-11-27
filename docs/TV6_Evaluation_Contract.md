# TV6 mục4 — evaluation records

API nội bộ evaluate_forecast_records trong backend/evaluation/forecast_records.py nhận prediction records, actual records, protocol đã xác minh, split và danh sách modes tường minh. Không gọi model, training hoặc fit; actual chỉ được ghép ở đây sau inference. Caller phải validate_protocol/artifact/source actual, hàm math không tự chứng nhận nguồn hay thời điểm test exposure.

Sau audit mục4, split val bắt buộc expected_validation_cohorts độc lập với rows đưa vào. Caller dùng load_validation_cohorts(root,protocol), helper đọc source JSON đã pin hash và tạo count/ordered-key hash. Không tự suy cohort từ prediction/actual đã bị lọc. Như vậy cả hai cùng thiếu mẫu vẫn bị từ chối, không gắn nhãn validation_full_set sai. Context này chỉ do backend tin cậy cung cấp, không lấy từ client. Protocol v1 giữ nguyên, không thêm/thay test cohort trong lock.

Actual có dataset_version/sample_id/forecast_origin/forecast_length/horizon_step/target_date/actual_price/split. Prediction giữ output contract mục3, không được kèm actual/error sẵn. Units/feature/protocol/run/model/seed/scaler/scope/release context phải đồng nhất; full model groups đủ3 seeds và baseline mỗi mode một lần. CSV seed42.0 được đọc về integer seed42, bool/seed lạ bị từ chối.

Keys được so đúng thứ tự, không tự sort/innerjoin/intersection. Thiếu/extra/duplicate/reordered records hoặc modes đều fail. Mỗi sample có đủ steps1..H, origin duy nhất và ngày tăng, target sau origin/trong split, ISO dates hợp lệ. Context model phải khớp catalog; baseline không có seed/run/checkpoint. Full-test cohort count/hash phải khớp protocol, các test kiểm logic này ở mục4 là fixture tổng hợp, chưa dùng actual test stock để tính metric.

MAE/RMSE gọi module one_step chung. H5 báo5 per-horizon và1 overall flattenN×5 residuals; không trung bình horizon RMSE. Overall có metric_scope=overall,horizon_step=None, không phải horizon0. sample_count=N windows, error_count=N×5; per-horizon error_count=N. H1 chỉ báoh1, không lặp overall giống h1. Không làm tròn trước metric và từ chối nonfinite derived metric/overflow.

Mean/std mẫu ddof1 trên metric từng seed trong cùng method/mode/horizon, không ensemble/pooling predictions. Baseline deterministic không giả lập3 seed hoặc std. DataFrames đầu vào không mutate; trả metrics,aggregates,residuals. Tổng9 neural runs và2 baseline mode trên validation tạo31 metric rows,8 aggregate rows,6.670 residual rows. Các rows có protocol ID/hash/split/currency/range_kind để tránh trộn kết quả.

split val dùng validation_full_set; split test chỉ được gắn official_full_set khi full cohort khớp protocol và nguồn đã được caller xác minh. Requested single-mode phải khai forecast_lengths=(1,) hoặc(5,), không tự suy mode từ dữ liệu thiếu. API selected_range/filter chưa triển khai trong mục4, không nhận subset rồi gắn nhãn full-set.

CLI scripts/check_tv6_evaluation.py chỉ tái dùng validation predictions mục3, raw actual từ prepared records đã pin. Baseline kiểm lại với raw last input, h1 MAE/RMSE đối chiếu TV5, file/source/protocol giữ hash. Không chạy inference hoặc metrics held-out test. Final workflow test thuộc mục5, sau nghiệm thu này.
