from __future__ import annotations

import hashlib
import json
import re
from importlib.metadata import version as package_version
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
    bad_format_count = int((~dates_str.str.fullmatch(DATE_PATTERN)).sum())
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

    if ticker != 'AAPL' or ('ticker' in df and not df['ticker'].eq('AAPL').all()):
        errors.append('Unexpected ticker; only AAPL is supported.')

    # Calendar-based coverage, including missing endpoints and non-session dates.
    # exchange_calendars maps NASDAQ to XNYS: record the actual reference explicitly.
    import exchange_calendars as xcals
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if start > end:
        raise ValueError('start_date must not exceed end_date')
    calendar = xcals.get_calendar('NASDAQ', start=start-pd.Timedelta(days=366), end=end+pd.Timedelta(days=366))
    expected = pd.DatetimeIndex(calendar.sessions_in_range(start,end)).tz_localize(None).normalize()
    observed = pd.DatetimeIndex(parsed_dates.dropna()).normalize().unique()
    missing_sessions = expected.difference(observed)
    unexpected_sessions = observed.difference(expected)
    if len(missing_sessions):
        errors.append(f'Missing trading sessions: {len(missing_sessions)}')
    if len(unexpected_sessions):
        errors.append(f'Unexpected non-session/out-of-range dates: {len(unexpected_sessions)}')
    calendar_report = {
        'requested_calendar':'NASDAQ', 'resolved_calendar':calendar.name,
        'library':'exchange_calendars', 'library_version':package_version('exchange_calendars'),
        'limitation':'NASDAQ is an alias of XNYS in this library; this is a reference session calendar, not independent Nasdaq certification.',
        'expected_session_count':len(expected),
        'missing_sessions':missing_sessions.strftime('%Y-%m-%d').tolist(),
        'unexpected_sessions':unexpected_sessions.strftime('%Y-%m-%d').tolist(),
        'coverage_by_year':[
            {'year':int(year), 'expected':int((expected.year==year).sum()), 'observed':int((observed.year==year).sum())}
            for year in range(start.year,end.year+1)
        ],
    }
    auxiliary = {}
    for column in ['Open','High','Low','Close','Volume']:
        if column in df:
            values = pd.to_numeric(df[column],errors='coerce')
            bad = ~np.isfinite(values) | (values < 0 if column == 'Volume' else values <= 0)
            auxiliary[column] = int(bad.sum())
            if bad.any():
                errors.append(f'Invalid auxiliary column {column}: {int(bad.sum())}')
    if all(column in df for column in ['Open','High','Low','Close']):
        ohlc = df[['Open','High','Low','Close']].apply(pd.to_numeric,errors='coerce')
        bad_ohlc = (ohlc.High < ohlc[['Open','Low','Close']].max(axis=1)) | (ohlc.Low > ohlc[['Open','High','Close']].min(axis=1))
        auxiliary['OHLC_inconsistent_rows'] = int(bad_ohlc.sum())
        if bad_ohlc.any():
            errors.append(f'Inconsistent OHLC rows: {int(bad_ohlc.sum())}')
    warnings = []
    large_moves = []
    if not errors:
        returns = adj_close.pct_change(fill_method=None)
        for index in df.index[returns.abs() > .10]:
            large_moves.append({'date':str(dates_str.loc[index]), 'return_pct':float(returns.loc[index]*100)})
        if large_moves:
            warnings.append(f'{len(large_moves)} absolute daily returns exceed 10%; retain rows and investigate in TV1 item 8.')

    # Thống kê số phiên theo từng giai đoạn Train (2015-2022), Val (2023), Test (2024-2025)
    years = parsed_dates.dt.year
    split_session_counts = {
        "train_2015_2022": int(((years >= 2015) & (years <= 2022)).sum()),
        "validation_2023": int((years == 2023).sum()),
        "test_2024_2025": int(((years >= 2024) & (years <= 2025)).sum()),
    }

    finite_prices = adj_close[np.isfinite(adj_close)]
    def price_stat(name):
        value = getattr(finite_prices, name)()
        return round(float(value), 6) if pd.notna(value) and np.isfinite(value) else None

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
        "non_finite_count": non_finite_count,
        "invalid_date_count": invalid_date_count,
        "bad_format_count": bad_format_count,
        "calendar": calendar_report,
        "auxiliary_invalid_counts": auxiliary,
        "warnings": warnings,
        "large_moves_for_review": large_moves,
        "rows_removed": 0,
        "non_positive_count": non_positive_count,
        "is_monotonic_increasing": is_monotonic_increasing,
        "split_session_counts": split_session_counts,
        "price_summary_usd": {
            "min": price_stat('min'),
            "max": price_stat('max'),
            "mean": price_stat('mean'),
            "std": price_stat('std'),
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
    validated_file = Path(validated_dir) / f'aapl_validated_{dataset_version}.csv'
    report_file = Path(metadata_dir) / f'aapl_validation_report_{dataset_version}.json'
    if validated_file.exists() or report_file.exists():
        raise FileExistsError('Validated snapshot/report already exists; do not overwrite. Audit existing data separately.')

    if not raw_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file snapshot gốc: {raw_file}")
    if not meta_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file metadata: {meta_file}")

    with meta_file.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    from backend.data.validation.provenance import inspect_snapshot_provenance

    provenance = inspect_snapshot_provenance(raw_file, metadata, dataset_version)
    if not provenance['passed']:
        raise ValueError(f"Metadata/provenance mismatch: {provenance['errors']}")

    raw_df = pd.read_csv(raw_file)
    report, validated_df = inspect_raw_dataframe(
        df=raw_df,
        dataset_version=dataset_version,
        ticker=metadata.get("ticker", "AAPL"),
    )
    report["validated_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["raw_sha256_verified"] = True
    report["provenance"] = provenance
    report["source_metadata_file"] = str(meta_file.as_posix())
    report["source_metadata_sha256"] = compute_sha256(meta_file)
    report["raw_sha256"] = provenance['raw_sha256']
    report["currency"] = metadata['currency']
    report["adjustment_policy"] = metadata['adjustment_policy']

    if not report["passed"]:
        raise ValueError(f"Dữ liệu không đạt kiểm tra validation: {report['errors']}")

    val_path_dir = Path(validated_dir)
    val_path_dir.mkdir(parents=True, exist_ok=True)
    validated_file = val_path_dir / f"aapl_validated_{dataset_version}.csv"
    report_file = Path(metadata_dir) / f"aapl_validation_report_{dataset_version}.json"
    streams, owned = [], []
    try:
        for path in (validated_file, report_file):
            stream = path.open('x', encoding='utf-8', newline='')
            streams.append(stream)
            owned.append(path)
        validated_df.to_csv(streams[0], index=False)
        streams[0].flush()
        report['validated_file'] = str(validated_file.as_posix())
        report['validated_sha256'] = compute_sha256(validated_file)
        report['validated_columns'] = list(validated_df.columns)
        json.dump(report, streams[1], ensure_ascii=False, indent=2)
        streams[1].flush()
    except BaseException:
        for stream in streams: stream.close()
        for path in owned: path.unlink()
        raise
    else:
        for stream in streams: stream.close()

    return report


if __name__ == "__main__":
    result = validate_aapl_dataset()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    val_df = pd.read_csv(result["validated_file"])
    print("\n--- 5 dòng đầu (data/validated) ---")
    print(val_df.head(5).to_string(index=False))
    print("\n--- 5 dòng cuối (data/validated) ---")
    print(val_df.tail(5).to_string(index=False))
