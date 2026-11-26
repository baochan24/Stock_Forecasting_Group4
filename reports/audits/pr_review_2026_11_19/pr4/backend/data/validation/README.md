
import pandas as pd
import hashlib

from pathlib import Path


def validate_dataset(
    raw_file_path: str
) -> dict:

    """
    Validate raw stock dataset.

    Checks:
    - Required columns
    - Missing values
    - Duplicate dates
    - Invalid dates
    - Invalid stock prices
    - Abnormal price values

    Returns:
        Validation report.
    """

    issues = []

    # 1. Read raw CSV
    file_path = Path(raw_file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {raw_file_path}"
        )

    df = pd.read_csv(file_path)

    # 2. Check required columns
    required_columns = [
        "date",
        "ticker",
        "adjusted_close"
    ]

    for column in required_columns:

        if column not in df.columns:

            issues.append({
                "type": "missing_column",
                "description": (
                    f"Missing column: {column}"
                ),
                "action": "Validation failed"
            })

    if any(
        item["type"] == "missing_column"
        for item in issues
    ):

        return {
            "is_valid": False,
            "validated_file_path": None,
            "num_rows": len(df),
            "issues": issues,
            "date_range": None,
            "hash": None
        }

    # 3. Convert date
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    invalid_dates = df["date"].isna().sum()

    if invalid_dates > 0:

        issues.append({
            "type": "invalid_date",
            "description": (
                f"{invalid_dates} invalid dates found"
            ),
            "action": "Remove invalid rows"
        })

        df = df.dropna(
            subset=["date"]
        )

    # 4. Check missing values
    missing_values = df[
        required_columns
    ].isna().sum()

    for column, count in missing_values.items():

        if count > 0:

            issues.append({
                "type": "missing_values",
                "description": (
                    f"{column}: {count} missing values"
                ),
                "action": "Remove invalid rows"
            })

    df = df.dropna(
        subset=required_columns
    )

    # 5. Check ticker
    invalid_ticker = df[
        df["ticker"] != "AAPL"
    ]

    if not invalid_ticker.empty:

        issues.append({
            "type": "invalid_ticker",
            "description": "Unexpected ticker found",
            "action": "Remove invalid rows"
        })

        df = df[
            df["ticker"] == "AAPL"
        ]

    # 6. Convert price to numeric
    df["adjusted_close"] = pd.to_numeric(
        df["adjusted_close"],
        errors="coerce"
    )

    invalid_prices = (
        df["adjusted_close"].isna()
        | (df["adjusted_close"] <= 0)
    )

    if invalid_prices.any():

        issues.append({
            "type": "invalid_price",
            "description": (
f"{invalid_prices.sum()} invalid prices found"
            ),
            "action": "Remove invalid rows"
        })

        df = df[
            ~invalid_prices
        ]

    # 7. Check duplicate dates
    duplicates = df.duplicated(
        subset=["date"],
        keep="first"
    )

    if duplicates.any():

        issues.append({
            "type": "duplicate_date",
            "description": (
                f"{duplicates.sum()} duplicate dates found"
            ),
            "action": "Keep first occurrence"
        })

        df = df.drop_duplicates(
            subset=["date"],
            keep="first"
        )

    # 8. Sort dates
    df = df.sort_values(
        "date"
    ).reset_index(drop=True)

    # 9. Check large date gaps
    if len(df) > 1:

        date_gaps = df["date"].diff().dt.days

        large_gaps = date_gaps[
            date_gaps > 7
        ]

        if not large_gaps.empty:

            issues.append({
                "type": "date_gap",
                "description": (
                    f"{len(large_gaps)} large date gaps found"
                ),
                "action": (
                    "Review against the official trading calendar"
                )
            })

    # 10. Check abnormal price changes
    price_changes = (
        df["adjusted_close"].pct_change().abs()
    )

    abnormal_changes = price_changes > 0.5

    if abnormal_changes.any():

        issues.append({
            "type": "abnormal_price_change",
            "description": (
                f"{abnormal_changes.sum()} price changes "
                "exceed 50 percent"
            ),
            "action": "Review suspicious observations"
        })

    # 11. Save validated dataset
    output_dir = Path("data/validated")

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir / "AAPL_validated.csv"
    )

    df["date"] = df["date"].dt.strftime(
        "%Y-%m-%d"
    )

    df.to_csv(
        output_file,
        index=False
    )

    # 12. Calculate SHA256
    file_hash = hashlib.sha256(
        output_file.read_bytes()
    ).hexdigest()

    # 13. Validation status
    is_valid = len(df) > 0

    # 14. Return report
    return {
        "is_valid": is_valid,
        "validated_file_path": str(output_file),
        "num_rows": len(df),
        "issues": issues,
        "date_range": (
            df["date"].iloc[0],
            df["date"].iloc[-1]
        ),
        "hash": file_hash
    }


if __name__ == "__main__":

    result = validate_dataset(
        "data/raw/AAPL_raw.csv"
    )

    print("VALIDATION RESULT")
    print(result)

