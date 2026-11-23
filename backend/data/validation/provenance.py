"""Check declared provenance against a local raw snapshot, without modifying it."""
from datetime import datetime, timedelta
from pathlib import Path
import re

import pandas as pd

from backend.data.validation.validator import compute_sha256


def inspect_snapshot_provenance(raw_file, metadata, dataset_version, project_root=None):
    root = Path(project_root or Path.cwd()).resolve()
    raw_file = Path(raw_file).resolve()
    errors = []
    checks = {}

    def check(name, passed):
        checks[name] = bool(passed)
        if not passed:
            errors.append(name)

    check('dataset_version', metadata.get('dataset_version') == dataset_version)
    check('ticker_AAPL', metadata.get('ticker') == 'AAPL')
    check('currency_USD', metadata.get('currency') == 'USD')
    check('source_Yahoo_yfinance', metadata.get('source') == 'Yahoo Finance (yfinance)')
    check('yfinance_version_present', isinstance(metadata.get('yfinance_version'), str) and metadata['yfinance_version'] not in ('', 'unknown'))
    check('requested_start_date', metadata.get('requested_start_date') == '2015-01-01')
    check('requested_end_date', metadata.get('requested_end_date') == '2025-12-31')
    try:
        downloaded = datetime.fromisoformat(metadata.get('downloaded_at_utc', ''))
        valid_timestamp = downloaded.utcoffset() == timedelta(0)
    except (ValueError, TypeError):
        valid_timestamp = False
    check('downloaded_at_UTC', valid_timestamp)
    policy = metadata.get('adjustment_policy', '')
    check('adjustment_policy', isinstance(policy, str) and 'auto_adjust=False' in policy and 'Adj Close' in policy)
    limitation = metadata.get('point_in_time_limitation')
    check('retrospective_limitation_present', isinstance(limitation, str) and bool(limitation.strip()))
    declared_path = metadata.get('raw_file')
    check('raw_file_path', isinstance(declared_path, str) and bool(declared_path) and (root / declared_path).resolve() == raw_file)
    actual_hash = compute_sha256(raw_file)
    declared_hash = metadata.get('raw_sha256')
    check('raw_SHA256', isinstance(declared_hash, str) and bool(re.fullmatch('[0-9a-f]{64}', declared_hash)) and declared_hash == actual_hash)
    df = pd.read_csv(raw_file)
    check('row_count', type(metadata.get('row_count')) is int and metadata['row_count'] == len(df) and len(df) > 0)
    check('columns_match', metadata.get('columns') == list(df.columns))
    check('raw_price_column', 'Adj Close' in df.columns)
    dates = pd.to_datetime(df.get('date', pd.Series(dtype=str)), errors='coerce')
    check('actual_date_bounds', not df.empty and len(dates) == len(df) and dates.notna().all() and metadata.get('actual_first_date') == str(df['date'].iloc[0]) and metadata.get('actual_last_date') == str(df['date'].iloc[-1]) and dates.min() >= pd.Timestamp('2015-01-01') and dates.max() <= pd.Timestamp('2025-12-31'))
    if 'ticker' in df:
        check('raw_ticker_consistent', df['ticker'].eq('AAPL').all())
    return {'passed':not errors, 'dataset_version':dataset_version, 'raw_sha256':actual_hash, 'checks':checks, 'errors':errors, 'scope':'Declared metadata consistency and local integrity; not independent source authentication, calendar completeness, or full data-quality validation.'}
