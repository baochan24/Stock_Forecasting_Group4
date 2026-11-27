# data/transforms

`anchored_price.py`: biểu diễn phát triển riêng origin-centered-price-delta-v1, nhận raw history/anchor và scale fit train, không fit. H1/H5 decode=P(origin)+scale*delta. Không thay scaling.py hoặc artifacts/contract TV2 v1. Xem docs/TV6_Residual_Development_v1.md.

## Mục 5 hoàn thành — 21/11/2026

Kiểm chứng scaler lưu sẵn `aapl_scaler_20261120T124720810874Z`: z=(P-mean_train)/scale_train, inverse P=z*scale_train+mean_train; không clip z âm/0, không làm tròn. Float64 roundtrip rtol=1e-12, atol=1e-12 USD trên fixture/snapshot đã thử; cast float32 cho model cần kiểm chứng riêng.

Test mới `tests/data/test_tv2_saved_scaling.py`: shapes `(B,30,1)/(B,1)/(B,5)` B=1/2; int/float32/float64→float64; view readonly/noncontiguous; không sửa input/state; scaler hằng scale=1 sau save/load; cấm fit/partial_fit. Suite TV2 28/28 đạt.

Lệnh: `.venv/tv2/Scripts/python.exe -X utf8 scripts/check_tv2_scaling.py --dataset-version aapl_2015_2025_acq_20261119T141302002415Z --scaler-dir artifacts/scalers/aapl_scaler_20261120T124720810874Z`. 12 checks đạt, max roundtrip error 5.684341886080802e-14 USD; hash scaler/manifest/5 artifacts nguồn không đổi. Evidence `logs/audit/tv2_scaling_20261121T014233722333Z/summary.json`. Mảng reshape thử shape không phải cửa sổ dự báo, không dùng training; windows còn mục 6–7.

Phép chuẩn hóa, inverse transform, tạo cửa sổ dùng chung. Không tự fit lại scaler.

Trạng thái: đã tiếp nhận `scale` và `inverse_scale` từ PR #3, commit `d52946b85a390d8af8d01c5ad7a7903a16ec8485`, vào `scaling.py`. Giữ thuật toán tác giả: reshape về một feature, transform/inverse_transform rồi khôi phục shape; không fit lại scaler. Mục 1 bổ sung validation và đổi tính toán sang float64 như mô tả dưới.

Dependencies: numpy và scikit-learn. Cần scaler đã fit trên train. Đã có kiểm tra đầu vào module nền; lưu/nạp và tích hợp TV2 còn chờ. Test tiếp nhận: `python -m unittest discover -s tests/data -p test_tv2_imported_code.py -v` từ gốc project, trong môi trường có numpy/pandas/scikit-learn.

Mục 1 cập nhật: `scale(values, scaler)` và `inverse_scale(values, scaler)` nhận mảng số thực hữu hạn, không rỗng, rank 1–3; trả float64 giữ nguyên shape. Không ép chuỗi/bool/complex thành giá. Không áp điều kiện dương cho transform vì giá trị chuẩn hóa có thể âm/0. Scaler phải là StandardScaler đã fit đúng một feature: sai kiểu báo TypeError, chưa fit báo sklearn NotFittedError, sai dữ liệu/feature hoặc kết quả không hữu hạn báo ValueError. Hai hàm không sửa input và không fit/refit scaler. Kiểm tra shape cụ thể của model sẽ thực hiện ở bước windowing/contract.
