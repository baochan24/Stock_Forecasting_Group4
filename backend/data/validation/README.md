# data/validation

Kiểm tra ngày, thiếu/trùng, giá trị; trả báo cáo và dữ liệu hợp lệ. Dùng chung phép kiểm tra với audit.

Trạng thái: vị trí triển khai dự kiến; chưa có code hoặc kiểm chứng. Chưa chọn tên file implementation để tránh tạo stub chạy giả.
Dataset validation for the Stock Forecasting Group4 project.

Expected input columns:
    date, ticker, adjusted_close

Run from the repository root:
    python backend/data/validation/dataset_validator.py

Or call:
    from backend.data.validation.dataset_validator import validate_dataset
    result = validate_dataset("data/raw/AAPL_raw.csv")
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = ["date", "ticker", "adjusted_close"]
DEFAULT_TICKER = "AAPL"
DEFAULT_MAX_DATE_GAP_DAYS = 7
DEFAULT_ABNORMAL_CHANGE_THRESHOLD = 0.50  # 50% absolute day-to-day change


def _issue(issue_type: str, description: str, action: str) -> dict[str, str]:
    """Create a consistently structured validation issue."""
    return {
        "type": issue_type,
        "description": description,
        "action": action,
    }


def _sha256_file(file_path: Path) -> str:
    """Return the SHA256 checksum of a file."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def validate_dataset(
    raw_file_path: str | Path,
    expected_ticker: str | None = DEFAULT_TICKER,
    output_dir: str | Path | None = None,
    max_date_gap_days: int = DEFAULT_MAX_DATE_GAP_DAYS,
    abnormal_change_threshold: float = DEFAULT_ABNORMAL_CHANGE_THRESHOLD,
) -> dict[str, Any]:
    """
    Validate and clean a raw stock CSV dataset.

    Checks:
      1. Input file and required columns
      2. Invalid dates
      3. Missing required values
      4. Unexpected ticker symbols
      5. Invalid/non-positive stock prices
      6. Duplicate dates
      7. Date gaps larger than the configured limit
      8. Abnormal day-to-day price changes

    Invalid rows are removed where appropriate. Suspicious price changes
    and large date gaps are reported for review, not automatically removed.

    is_valid is True only when no validation issues were found.
    A cleaned CSV may still be saved when non-fatal issues were found.
    """

    issues: list[dict[str, str]] = []
    raw_path = Path(raw_file_path)

    # 1. Read raw CSV
    if not raw_path.is_file():
        return {
            "is_valid": False,
            "validated_file_path": None,
            "num_rows": 0,
            "issues": [_issue(
                "file_not_found",
                f"File not found: {raw_path}",
                "Check the input file path.",
            )],
            "date_range": None,
            "hash": None,
        }

    try:
        df = pd.read_csv(raw_path)
    except (pd.errors.ParserError, UnicodeDecodeError, OSError) as exc:
        return {
            "is_valid": False,
            "validated_file_path": None,
            "num_rows": 0,
            "issues": [_issue(
                "read_error",
                f"Could not read CSV file: {exc}",
"Check that the file is a valid CSV.",
            )],
            "date_range": None,
            "hash": None,
        }

    # Normalize column names and ticker values
    df.columns = df.columns.astype(str).str.strip().str.lower()

    # 2. Check required columns
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]

    if missing_columns:
        for column in missing_columns:
            issues.append(_issue(
                "missing_column",
                f"Missing required column: {column}",
                "Add the required column to the CSV file.",
            ))

        return {
            "is_valid": False,
            "validated_file_path": None,
            "num_rows": len(df),
            "issues": issues,
            "date_range": None,
            "hash": None,
        }

    # 3. Convert and validate dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = int(df["date"].isna().sum())

    if invalid_dates:
        issues.append(_issue(
            "invalid_date",
            f"{invalid_dates} invalid date values found.",
            "Remove rows with invalid dates.",
        ))
        df = df.dropna(subset=["date"]).copy()

    # 4. Check missing required values
    missing_counts = df[REQUIRED_COLUMNS].isna().sum()

    for column, count in missing_counts.items():
        if int(count) > 0:
            issues.append(_issue(
                "missing_values",
                f"{int(count)} missing values found in column '{column}'.",
                "Remove rows with missing required values.",
            ))

    df = df.dropna(subset=REQUIRED_COLUMNS).copy()

    # 5. Validate ticker symbols
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    if expected_ticker:
        expected_ticker = expected_ticker.strip().upper()
        invalid_ticker = df["ticker"] != expected_ticker
        invalid_ticker_count = int(invalid_ticker.sum())

        if invalid_ticker_count:
            issues.append(_issue(
                "invalid_ticker",
                f"{invalid_ticker_count} rows contain unexpected ticker symbols.",
                f"Keep only ticker '{expected_ticker}'.",
            ))
            df = df.loc[~invalid_ticker].copy()

    # 6. Convert stock prices to numeric and validate them
    df["adjusted_close"] = pd.to_numeric(
        df["adjusted_close"], errors="coerce"
    )

    invalid_prices = (
        df["adjusted_close"].isna()
        | (df["adjusted_close"] <= 0)
    )
    invalid_price_count = int(invalid_prices.sum())

    if invalid_price_count:
        issues.append(_issue(
            "invalid_stock_price",
            f"{invalid_price_count} invalid or non-positive stock prices found.",
            "Remove rows with invalid adjusted_close values.",
        ))
        df = df.loc[~invalid_prices].copy()

    # 7. Check and remove duplicate dates
duplicate_mask = df.duplicated(subset=["date"], keep="first")
    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count:
        issues.append(_issue(
            "duplicate_date",
            f"{duplicate_count} duplicate dates found.",
            "Keep the first occurrence of each date.",
        ))
        df = df.drop_duplicates(subset=["date"], keep="first").copy()

    # 8. Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    # 9. Check large gaps between dates
    if len(df) > 1:
        date_gaps = df["date"].diff().dt.days
        large_gaps = date_gaps[date_gaps > max_date_gap_days]

        if not large_gaps.empty:
            issues.append(_issue(
                "date_gap",
                f"{len(large_gaps)} large date gaps found "
                f"(more than {max_date_gap_days} days).",
                "Review the official trading calendar and source data.",
            ))

    # 10. Check abnormal price changes
    if len(df) > 1:
        price_changes = df["adjusted_close"].pct_change().abs()
        abnormal_changes = price_changes[
            price_changes > abnormal_change_threshold
        ]

        if not abnormal_changes.empty:
            issues.append(_issue(
                "abnormal_price_change",
                f"{len(abnormal_changes)} abnormal price changes found "
                f"(greater than {abnormal_change_threshold:.0%}).",
                "Review suspicious observations against a reliable source.",
            ))

    # Stop if no usable rows remain
    if df.empty:
        issues.append(_issue(
            "empty_dataset",
            "No valid rows remain after cleaning.",
            "Check the source CSV and validation rules.",
        ))
        return {
            "is_valid": False,
            "validated_file_path": None,
            "num_rows": 0,
            "issues": issues,
            "date_range": None,
            "hash": None,
        }

    # 11. Save validated dataset
    if output_dir is None:
        # dataset_validator.py is expected at:
        # <project_root>/backend/data/validation/dataset_validator.py
        project_root = Path(__file__).resolve().parents[3]
        output_path = project_root / "data" / "validated"
    else:
        output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    ticker_name = expected_ticker or str(df["ticker"].iloc[0])
    output_file = output_path / f"{ticker_name.upper()}_validated.csv"

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_csv(output_file, index=False)

    # 12. Calculate SHA256 checksum of the saved file
    file_hash = _sha256_file(output_file)

    # 13. Return validation report
    return {
        "is_valid": len(issues) == 0,
        "validated_file_path": str(output_file),
        "num_rows": len(df),
        "issues": issues,
        "date_range": {
            "start": str(df["date"].iloc[0]),
            "end": str(df["date"].iloc[-1]),
},
        "hash": file_hash,
    }


if __name__ == "__main__":
    # Run from the repository root.
    result = validate_dataset("data/raw/AAPL_raw.csv")

    print("\n========== VALIDATION RESULT ==========")
    print(f"Valid: {result['is_valid']}")
    print(f"Output file: {result['validated_file_path']}")
    print(f"Number of rows: {result['num_rows']}")
    print(f"Date range: {result['date_range']}")
    print(f"SHA256: {result['hash']}")
    print("Issues:")

    if result["issues"]:
        for item in result["issues"]:
            print(
                f"- [{item['type']}] {item['description']} "
                f"| Action: {item['action']}"
            )
    else:
        print("- No issues found.")

