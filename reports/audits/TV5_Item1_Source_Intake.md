# TV5 mục 1 — tiếp nhận CNN và baseline

Ngày 26/11/2026. Tiếp nhận ba file nguyên nội dung từ commit edc2bd953c7644040f4142a545316377cd143e13 của PR #9 tại đúng đường dẫn.

- backend/models/cnn_one_step/model.py
- backend/models/cnn_one_step/__init__.py
- tests/models/test_cnn_one_step.py

Đã lưu SHA256 nguồn, commit và hash bảo vệ các module TV1–TV4 cùng notebook có trước. Sau thực thi, ba file tiếp nhận vẫn khớp nguồn, các file bảo vệ không thay đổi. [Receipt tiếp nhận](../../logs/audit/tv5_item1_20261126T030327572216Z/intake.json)

## Kiểm chứng trong workspace

Dùng Python .venv/tv4_clean, môi trường đã kiểm chứng của TV4, không cài thêm dependency. Tests chạy trong subprocess từ workspace, 7/7 đạt và không skip. Notebook dùng kernel riêng aapl-coursework-tv5 trỏ đúng Python này. Source CNN import từ backend workspace. [JUnit và pytest log](../../logs/audit/tv5_tests_20261126T030527656075Z/) · [Receipt tests](../../logs/audit/tv5_tests_20261126T030527656075Z/summary.json)

Forward diagnostic dùng hai cửa sổ tensor tổng hợp (2,30,1), output (2,1) hữu hạn. CNN có 17.057 tham số, dtype float32 theo source tác giả. Trọng số khởi tạo bằng seed cố định phục vụ quan sát shape/kiến trúc.

Notebook 05 đã thực thi 4/4 code cell, lưu bảng file/hash, từng testcase, cấu trúc model, shape và bằng chứng bảo vệ source. [Biên bản notebook](../../logs/audit/member_notebooks_20261126T030505976410Z/summary.json)

## Phạm vi tiếp theo

Mục 1 hoàn thành tiếp nhận và baseline. Các vấn đề output_size=5, dtype với dữ liệu TV2, finite guards và persistence chưa được sửa ở bước này. Mục 2 sẽ chốt kiến trúc/dtype/contract. Các phần kết nối dữ liệu thật, training, checkpoint và kết quả thực nghiệm vẫn chờ theo flow.
