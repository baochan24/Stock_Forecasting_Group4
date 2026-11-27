from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import certifi

# Xử lý lỗi đường dẫn chứa ký tự tiếng Việt trên Windows cho thư viện mạng của yfinance
_cert_path = certifi.where()
if not _cert_path.isascii():
    _ascii_cert = Path(tempfile.gettempdir()) / "yf_cacert.pem"
    shutil.copy2(_cert_path, _ascii_cert)
    os.environ["CURL_CA_BUNDLE"] = str(_ascii_cert)
    os.environ["SSL_CERT_FILE"] = str(_ascii_cert)

import pandas as pd
import yfinance as yf


def compute_sha256(file_path: Path) -> str:
    """Tính mã băm SHA-256 của file snapshot để kiểm tra tính toàn vẹn."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_aapl_snapshot(
    dataset_version: str = "aapl_2015_2025_v1",
    raw_dir: str | Path = "data/raw",
    metadata_dir: str | Path = "data/metadata",
) -> dict[str, Any]:
    """Tải dữ liệu AAPL (2015-2025) từ Yahoo Finance, lưu bản gốc và metadata."""
    ticker = "AAPL"
    start_date = "2015-01-01"
    end_date_inclusive = "2025-12-31"
    yf_end_date = "2026-01-01"  # end trong yfinance không bao gồm ngày kết thúc

    raw_path_dir = Path(raw_dir)
    meta_path_dir = Path(metadata_dir)
    raw_path_dir.mkdir(parents=True, exist_ok=True)
    meta_path_dir.mkdir(parents=True, exist_ok=True)

    df = yf.download(
        tickers=ticker,
        start=start_date,
        end=yf_end_date,
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        raise RuntimeError("Không tải được dữ liệu AAPL từ Yahoo Finance (DataFrame rỗng).")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    df["date"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d")

    df = df[(df["date"] >= start_date) & (df["date"] <= end_date_inclusive)].copy()
    ordered_cols = ["date"] + [c for c in df.columns if c not in ("date", date_col)]
    df = df[ordered_cols]

    raw_file_path = raw_path_dir / f"aapl_raw_{dataset_version}.csv"
    df.to_csv(raw_file_path, index=False)

    file_hash = compute_sha256(raw_file_path)
    downloaded_at = datetime.now(timezone.utc).isoformat()

    metadata: dict[str, Any] = {
        "dataset_version": dataset_version,
        "ticker": ticker,
        "source": "Yahoo Finance (yfinance)",
        "yfinance_version": getattr(yf, "__version__", "unknown"),
        "downloaded_at_utc": downloaded_at,
        "currency": "USD",
        "requested_start_date": start_date,
        "requested_end_date": end_date_inclusive,
        "actual_first_date": str(df["date"].iloc[0]),
        "actual_last_date": str(df["date"].iloc[-1]),
        "row_count": int(len(df)),
        "columns": list(df.columns),
        "adjustment_policy": (
            "auto_adjust=False; su dung cot 'Adj Close' lam adjusted_close "
            "(da dieu chinh chia tach co phieu va co tuc boi Yahoo Finance)."
        ),
        "point_in_time_limitation": (
            "Gia dong cua da dieu chinh tren Yahoo Finance bi dieu chinh hoi cuu "
            "tai thoi diem tai du lieu, khong phan anh gia point-in-time tai qua khu."
        ),
        "raw_file": str(raw_file_path.as_posix()),
        "raw_sha256": file_hash,
    }

    meta_file_path = meta_path_dir / f"aapl_metadata_{dataset_version}.json"
    with meta_file_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata


if __name__ == "__main__":
    meta = download_aapl_snapshot()
    print(json.dumps(meta, ensure_ascii=False, indent=2))
