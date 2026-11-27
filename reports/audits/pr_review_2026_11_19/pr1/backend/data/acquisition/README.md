import yfinance as yf
import pandas as pd
import hashlib
import json

from pathlib import Path
from datetime import datetime, timezone


def download_aapl_data(
    start_date: str,
    end_date: str,
    save_dir: str
) -> dict:

    """
    Download AAPL stock data from Yahoo Finance.

    Args:
        start_date: Start date, example "2015-01-01"
        end_date: End date, example "2025-12-31"
        save_dir: Directory to save raw CSV data.

    Returns:
        Dictionary containing file path, number of rows,
        date range, SHA256 hash and download timestamp.
    """

    # 1. Validate dates
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    if start >= end:
        raise ValueError("start_date must be before end_date")

    # yfinance uses exclusive end date
    end_exclusive = end + pd.Timedelta(days=1)

    # 2. Create output directory
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    # 3. Download stock data
    df = yf.download(
        "AAPL",
        start=start_date,
        end=end_exclusive.strftime("%Y-%m-%d"),
        auto_adjust=False,
        progress=False
    )

    if df.empty:
        raise ValueError("No stock data downloaded.")

    # 4. Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Adj Close" not in df.columns:
        raise ValueError("Adjusted Close column not found.")

    # 5. Prepare dataset
    df = df.reset_index()

    df = df[["Date", "Adj Close"]]

    df = df.rename(columns={
        "Date": "date",
        "Adj Close": "adjusted_close"
    })

    df["date"] = pd.to_datetime(
        df["date"]
    ).dt.strftime("%Y-%m-%d")

    df["ticker"] = "AAPL"

    df = df[
        ["date", "ticker", "adjusted_close"]
    ]

    # 6. Remove invalid prices
    df["adjusted_close"] = pd.to_numeric(
        df["adjusted_close"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["adjusted_close"]
    )

    # 7. Sort data
    df = df.sort_values("date")

    # 8. Save CSV
    file_path = save_path / "AAPL_raw.csv"

    df.to_csv(
        file_path,
        index=False
    )

    # 9. Calculate SHA256
    file_hash = hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()

    # 10. Save metadata
    metadata = {
        "ticker": "AAPL",
        "source": "Yahoo Finance",
        "adjustment_policy": (
            "Uses Yahoo Finance Adj Close "
            "with auto_adjust=False"
        ),
        "requested_start_date": start_date,
        "requested_end_date": end_date,
        "download_timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "sha256": file_hash
    }

    metadata_path = save_path / "AAPL_metadata.json"

    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False
)

    # 11. Return result
    return {
        "file_path": str(file_path),
        "num_rows": len(df),
        "date_range": (
            df["date"].iloc[0],
            df["date"].iloc[-1]
        ),
        "hash": file_hash,
        "download_timestamp": metadata[
            "download_timestamp"
        ]
    }


if __name__ == "__main__":

    result = download_aapl_data(
        start_date="2015-01-01",
        end_date="2025-12-31",
        save_dir="data/raw"
    )

    print("DOWNLOAD COMPLETED")
    print(result)

