from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EXPECTED_VALIDATED_COLUMNS = ["date", "ticker", "adjusted_close", "dataset_version"]


def compute_sha256(file_path: Path) -> str:
    """Tính mã băm SHA-256 của file để đối chiếu tính toàn vẹn."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def inspect_raw_dataframe(
    df: pd.DataFrame,
    dataset_version: str,
    ticker: str = "AAPL",
    start_date: str = "2015-01-01",
    end_date: str = "2025-12-31",
) -> tuple[dict[str, Any], pd.DataFrame]:
    """
    Hàm kiểm tra dữ liệu dùng chung cho cả validation và audit.
    Không âm thầm sửa dữ liệu; trả về báo cáo kiểm tra và DataFrame hợp lệ.
    """
    errors: list[str] = []

    # 1. Kiểm tra cột bắt buộc
    required_cols = {"date", "Adj Close"}
    missing_cols = sorted(required_cols - set(df.columns))
    if missing_cols:
        errors.append(f"Thiếu cột bắt buộc trong dữ liệu gốc: {missing_cols}")
        return {"passed": False, "errors": errors}, pd.DataFrame(columns=EXPECTED_VALIDATED_COLUMNS)

    if df.empty:
        errors.append("Bảng dữ liệu rỗng.")
        return {"passed": False, "errors": errors}, pd.DataFrame(columns=EXPECTED_VALIDATED_COLUMNS)

    # 2. Kiểm tra định dạng ngày YYYY-MM-DD và tính hợp lệ của ngày lịch
    dates_str = df["date"].astype(str)
    bad_format_count = int((~dates_str.str.match(DATE_PATTERN)).sum())
    parsed_dates = pd.to_datetime(dates_str, format="%Y-%m-%d", errors="coerce")
    invalid_date_count = int(parsed_dates.isna().sum())

    if bad_format_count > 0 or invalid_date_count > 0:
        errors.append(
            f"Lỗi định dạng hoặc ngày không hợp lệ: bad_format={bad_format_count}, invalid_date={invalid_date_count}"
        )

    # 3. Kiểm tra trùng lặp ngày và thứ tự thời gian tăng dần
    duplicate_date_count = int(dates_str.duplicated().sum())
    is_monotonic_increasing = bool(parsed_dates.is_monotonic_increasing)
    if duplicate_date_count > 0:
        errors.append(f"Phát hiện {duplicate_date_count} dòng bị trùng ngày giao dịch.")
    if not is_monotonic_increasing:
        errors.append("Thứ tự ngày giao dịch không tăng dần nghiêm ngặt.")

    # 4. Kiểm tra phạm vi ngày 2015-2025
    min_date = str(dates_str.min())
    max_date = str(dates_str.max())
    if min_date < start_date or max_date > end_date:
        errors.append(f"Ngày nằm ngoài phạm vi {start_date}..{end_date}: [{min_date}, {max_date}]")

    # 5. Kiểm tra giá trị Adj Close (thiếu, vô cực, <= 0)
    adj_close = pd.to_numeric(df["Adj Close"], errors="coerce")
    missing_price_count = int(adj_close.isna().sum())
    non_finite_count = int((~np.isfinite(adj_close.fillna(1.0))).sum())
    non_positive_count = int((adj_close <= 0).sum())

    if missing_price_count > 0:
        errors.append(f"Có {missing_price_count} giá trị Adj Close bị thiếu (NaN).")
    if non_finite_count > 0:
        errors.append(f"Có {non_finite_count} giá trị Adj Close không hữu hạn (Inf/-Inf).")
    if non_positive_count > 0:
        errors.append(f"Có {non_positive_count} giá trị Adj Close <= 0.")

    # Thống kê số phiên theo từng giai đoạn Train (2015-2022), Val (2023), Test (2024-2025)
    years = parsed_dates.dt.year
    split_session_counts = {
        "train_2015_2022": int(((years >= 2015) & (years <= 2022)).sum()),
        "validation_2023": int((years == 2023).sum()),
        "test_2024_2025": int(((years >= 2024) & (years <= 2025)).sum()),
    }

    passed = len(errors) == 0
    report: dict[str, Any] = {
        "passed": passed,
        "dataset_version": dataset_version,
        "ticker": ticker,
        "row_count": int(len(df)),
        "first_date": min_date,
        "last_date": max_date,
        "duplicate_date_count": duplicate_date_count,
        "missing_price_count": missing_price_count,
        "non_positive_count": non_positive_count,
        "is_monotonic_increasing": is_monotonic_increasing,
        "split_session_counts": split_session_counts,
        "price_summary_usd": {
            "min": round(float(adj_close.min()), 6),
            "max": round(float(adj_close.max()), 6),
            "mean": round(float(adj_close.mean()), 6),
            "std": round(float(adj_close.std()), 6),
        },
        "errors": errors,
    }

    if not passed:
        return report, pd.DataFrame(columns=EXPECTED_VALIDATED_COLUMNS)

    # Tạo bảng chuẩn 4 cột theo đúng Data Flow Contract
    validated_df = pd.DataFrame(
        {
            "date": dates_str,
            "ticker": ticker,
            "adjusted_close": adj_close.astype(float),
            "dataset_version": dataset_version,
        }
    )
    return report, validated_df


def validate_aapl_dataset(
    dataset_version: str = "aapl_2015_2025_v1",
    raw_dir: str | Path = "data/raw",
    validated_dir: str | Path = "data/validated",
    metadata_dir: str | Path = "data/metadata",
) -> dict[str, Any]:
    """Đọc snapshot gốc, đối chiếu hash, chạy kiểm tra và lưu bảng dữ liệu sạch."""
    raw_file = Path(raw_dir) / f"aapl_raw_{dataset_version}.csv"
    meta_file = Path(metadata_dir) / f"aapl_metadata_{dataset_version}.json"

    if not raw_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file snapshot gốc: {raw_file}")
    if not meta_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file metadata: {meta_file}")

    with meta_file.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    actual_raw_hash = compute_sha256(raw_file)
    expected_raw_hash = metadata.get("raw_sha256")
    if actual_raw_hash != expected_raw_hash:
        raise ValueError(
            f"Sai lệch SHA-256 của file raw! Mong đợi: {expected_raw_hash}, thực tế: {actual_raw_hash}"
        )

    raw_df = pd.read_csv(raw_file)
    report, validated_df = inspect_raw_dataframe(
        df=raw_df,
        dataset_version=dataset_version,
        ticker=metadata.get("ticker", "AAPL"),
    )
    report["validated_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["raw_sha256_verified"] = True

    if not report["passed"]:
        raise ValueError(f"Dữ liệu không đạt kiểm tra validation: {report['errors']}")

    val_path_dir = Path(validated_dir)
    val_path_dir.mkdir(parents=True, exist_ok=True)
    validated_file = val_path_dir / f"aapl_validated_{dataset_version}.csv"
    validated_df.to_csv(validated_file, index=False)

    report["validated_file"] = str(validated_file.as_posix())
    report["validated_sha256"] = compute_sha256(validated_file)
    report["validated_columns"] = list(validated_df.columns)

    report_file = Path(metadata_dir) / f"aapl_validation_report_{dataset_version}.json"
    with report_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


if __name__ == "__main__":
    result = validate_aapl_dataset()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    val_df = pd.read_csv(result["validated_file"])
    print("\n--- 5 dòng đầu (data/validated) ---")
    print(val_df.head(5).to_string(index=False))
    print("\n--- 5 dòng cuối (data/validated) ---")
    print(val_df.tail(5).to_string(index=False))