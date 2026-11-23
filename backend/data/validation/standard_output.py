"""Read-only acceptance of the standard table after the raw quality audit."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

from backend.data.validation.validator import EXPECTED_VALIDATED_COLUMNS, compute_sha256
from backend.data.validation.provenance import inspect_snapshot_provenance


def inspect_standard_output(raw_file, metadata_file, validated_file, validation_file,
                            quality_file, dataset_version, project_root=None):
    paths = [Path(p) for p in [raw_file,metadata_file,validated_file,validation_file,quality_file]]
    raw_path, meta_path, val_path, report_path, audit_path = paths
    meta, report, quality = [json.loads(p.read_text(encoding='utf-8')) for p in [meta_path,report_path,audit_path]]
    hashes = {key:compute_sha256(path) for key,path in zip(['raw','metadata','validated','validation_report','quality_audit'],paths)}
    checks = {}
    def check(name, condition): checks[name] = bool(condition)
    provenance = inspect_snapshot_provenance(raw_path,meta,dataset_version,project_root)
    check('source_provenance',provenance['passed'])
    check('quality_passed_for_same_snapshot',quality.get('passed') is True and quality.get('dataset_version')==dataset_version and quality.get('raw_sha256')==hashes['raw'] and quality.get('source_metadata_sha256')==hashes['metadata'])
    check('validation_passed_for_same_version',report.get('passed') is True and report.get('dataset_version')==dataset_version and report.get('provenance',{}).get('passed') is True)
    check('validation_source_hashes',report.get('raw_sha256')==hashes['raw'] and report.get('source_metadata_sha256')==hashes['metadata'])
    check('validated_hash',report.get('validated_sha256')==hashes['validated'])
    root = Path(project_root or Path.cwd())
    check('validated_path_link',isinstance(report.get('validated_file'),str) and (root/report['validated_file']).resolve()==val_path.resolve())
    raw, val = pd.read_csv(raw_path), pd.read_csv(val_path)
    check('exact_four_column_schema',list(val.columns)==EXPECTED_VALIDATED_COLUMNS and report.get('validated_columns')==EXPECTED_VALIDATED_COLUMNS)
    check('row_count_preserved',len(raw)==len(val)==meta.get('row_count')==report.get('row_count') and len(val)>0)
    if set(EXPECTED_VALIDATED_COLUMNS).issubset(val.columns):
        dates = pd.to_datetime(val.date,format='%Y-%m-%d',errors='coerce')
        check('dates_valid_unique_ordered',val.date.astype(str).str.fullmatch(r'\d{4}-\d{2}-\d{2}').all() and dates.notna().all() and dates.is_monotonic_increasing and not dates.duplicated().any())
        check('all_rows_AAPL',val.ticker.eq('AAPL').all())
        check('all_rows_same_dataset_version',val.dataset_version.eq(dataset_version).all())
        prices=pd.to_numeric(val.adjusted_close,errors='coerce').to_numpy()
        check('prices_finite_positive',np.isfinite(prices).all() and (prices>0).all())
        check('dates_match_raw_in_order',len(raw)==len(val) and val.date.tolist()==raw.date.tolist())
        raw_prices=pd.to_numeric(raw['Adj Close'],errors='coerce').to_numpy()
        check('prices_match_Adj_Close_USD',len(raw)==len(val) and np.allclose(prices,raw_prices,rtol=1e-12,atol=1e-12,equal_nan=False))
    errors=[name for name,passed in checks.items() if not passed]
    return {'passed':not errors,'dataset_version':dataset_version,'checks':checks,'errors':errors,'hashes':hashes,'raw_rows':len(raw),'validated_rows':len(val),'schema':list(val.columns),'price_unit':'USD (declared source metadata)','mapping':'raw.date -> date; AAPL -> ticker; raw.Adj Close -> adjusted_close; source dataset_version -> dataset_version','transformations':'No dropping, filling, rescaling, rounding, splitting or windowing; other OHLCV columns remain in raw.','tolerance':{'rtol':1e-12,'atol':1e-12},'recipient_verified':False}
