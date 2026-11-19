"""Re-audit TV1 artifacts and acceptance evidence without changing the dataset."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys
from unittest.mock import patch
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.acquisition.downloader import download_aapl_snapshot
from backend.data.validation.provenance import inspect_snapshot_provenance
from backend.data.validation.standard_output import inspect_standard_output
from backend.data.validation.validator import inspect_raw_dataframe,compute_sha256
from scripts.verify_tv1_handoff import verify

def latest(pattern,version):
    matches=[]
    for path in sorted(ROOT.glob(pattern)):
        data=json.loads(path.read_text(encoding='utf-8'))
        if data.get('dataset_version')==version:matches.append((path,data))
    if not matches:raise FileNotFoundError(pattern)
    return matches[-1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-version',required=True)
    args=parser.parse_args();version=args.dataset_version
    if not version or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in version):raise ValueError('Invalid version')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'data/metadata'/f'tv1_final_audit_{stamp}';out.mkdir(exist_ok=False)
    raw_path=ROOT/f'data/raw/aapl_raw_{version}.csv';meta_path=ROOT/f'data/metadata/aapl_metadata_{version}.json'
    val_path=ROOT/f'data/validated/aapl_validated_{version}.csv';report_path=ROOT/f'data/metadata/aapl_validation_report_{version}.json'
    protected=[raw_path,meta_path,val_path,report_path]
    before={p.relative_to(ROOT).as_posix():compute_sha256(p) for p in protected}
    raw=pd.read_csv(raw_path);val=pd.read_csv(val_path);meta=json.loads(meta_path.read_text(encoding='utf-8'))
    provenance=inspect_snapshot_provenance(raw_path,meta,version,ROOT)
    quality,_=inspect_raw_dataframe(raw,version)
    quality.update(raw_sha256=compute_sha256(raw_path),source_metadata_sha256=compute_sha256(meta_path))
    quality_path=out/'quality.json';quality_path.write_text(json.dumps(quality,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    standard=inspect_standard_output(raw_path,meta_path,val_path,report_path,quality_path,version,ROOT)
    receipt=json.loads((ROOT/f'data/metadata/aapl_handoff_{version}_complete.json').read_text(encoding='utf-8'))
    archive=ROOT/receipt['archive'];handoff=verify(archive,archive.with_suffix('.zip.sha256'))
    protected_version=False
    with patch('backend.data.acquisition.downloader.yf.download') as network:
        try:download_aapl_snapshot(version,raw_path.parent,meta_path.parent)
        except FileExistsError:protected_version=True
        network.assert_not_called()
    test_path,tests=latest('logs/audit/tv1_tests_*/summary.json',version)
    source_current=all(compute_sha256(ROOT/path)==digest for path,digest in tests.get('source_hashes',{}).items()) and bool(tests.get('source_hashes'))
    tests_pass=tests['passed'] and not tests['skipped'] and source_current and compute_sha256(ROOT/tests['log_file'])==tests['unittest_log_sha256']
    eda_path,eda=latest(f'data/metadata/eda/{version}/*/exploration_summary.json',version)
    eda_pass=eda['raw_sha256']==compute_sha256(raw_path) and eda['validated_sha256']==compute_sha256(val_path) and eda['rows']==len(raw) and all((ROOT/name).is_file() for name in eda['figures'])
    anomaly_path,anomaly=latest(f'data/metadata/eda/{version}/*/anomaly_review/anomaly_review.json',version)
    ledger_path=ROOT/'reports/audits/TV1_Anomaly_Sources.json';ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    returns=val.adjusted_close.pct_change(fill_method=None)
    flag_dates=val.loc[returns.abs()>.10,'date'].tolist()
    anomaly_pass=anomaly['raw_sha256']==compute_sha256(raw_path) and anomaly['sources_sha256']==compute_sha256(ledger_path) and set(flag_dates)=={x['date'] for x in anomaly['events']}=={x['date'] for x in ledger['events']} and anomaly['rows_removed']==0 and anomaly['values_changed']==0
    reproduction=json.loads((ROOT/'data/metadata/tv1_reproducibility_latest.json').read_text(encoding='utf-8'))
    repro_source_match=all(compute_sha256(ROOT/path)==digest for path,digest in reproduction['source_hashes'].items() if path.startswith(('backend/data/','tests/data/')) and path.endswith('.py'))
    local_repro=reproduction['passed'] and reproduction['dataset_version']==version and reproduction['notebook_passed'] and repro_source_match
    required_docs=['docs/TV1_Setup_and_Reproduce.md','notebooks/requirements-eda.txt','notebooks/requirements-tv1-lock.txt','reports/02_Data_Description.md','reports/03_Implementation.md','reports/04_Setup_and_Run.md']
    docs_present=all((ROOT/path).is_file() for path in required_docs)
    drive=json.loads((ROOT/'data/metadata/tv1_drive_audit_20261119.json').read_text(encoding='utf-8'))
    drive_verified=all(item['status']=='fulfilled' and drive['folder_id'] in (item.get('result') or {}).get('parent_ids',[]) for item in drive['files'])
    checks=[provenance['passed'],handoff['passed'] and drive_verified,provenance['passed'],protected_version,quality['passed'],standard['passed'],eda_pass,anomaly_pass,tests_pass,local_repro and docs_present]
    names=['Thu thập dữ liệu','Bàn giao snapshot','Metadata và nguồn gốc','Bảo vệ phiên bản','Kiểm tra chất lượng','Xuất/xác minh dữ liệu chuẩn','Khám phá dữ liệu','Điều tra bất thường','Kiểm thử','Tài liệu và tái lập']
    matrix=[]
    for i,(name,passed) in enumerate(zip(names,checks),start=1):
        status='Đạt cục bộ' if passed else 'Cần xử lý'
        if passed and i in (2,10):status='Đạt phần cung cấp/cục bộ; chờ xác nhận độc lập'
        matrix.append({'item':i,'name':name,'local_passed':bool(passed),'status':status})
    after={p.relative_to(ROOT).as_posix():compute_sha256(p) for p in protected}
    if before!=after:raise ValueError('Audit changed protected artifacts')
    prices=val.adjusted_close
    result={'audit_run_id':stamp,'dataset_version':version,'all_local_requirements_passed':all(checks),'ready_for_TV2_locally':all(checks),'fully_accepted':False,'independent_recipient_verified':False,'local_completed_items':8 if all(checks) else sum(checks[i] for i in range(10) if i not in [1,9]),'conditional_items':[2,10],'matrix':matrix,'data':{'raw_rows':len(raw),'validated_rows':len(val),'first_date':val.date.iloc[0],'last_date':val.date.iloc[-1],'schema':list(val.columns),'split_session_counts':quality['split_session_counts'],'return_count':int(returns.notna().sum()),'price_summary_usd':prices.describe().to_dict(),'return_summary_pct':(returns.dropna()*100).describe(percentiles=[.01,.99]).to_dict(),'flagged_dates':flag_dates,'missing_sessions':quality['calendar']['missing_sessions'],'unexpected_sessions':quality['calendar']['unexpected_sessions'],'rows_removed':0},'artifact_hashes':after,'artifacts_unchanged':before==after,'provenance':provenance,'quality':quality,'standard_output':standard,'handoff':handoff,'drive_metadata_verified':drive_verified,'test_evidence':test_path.relative_to(ROOT).as_posix(),'tests_run':tests['tests_run'],'test_failures':tests['failures'],'test_errors':tests['errors'],'test_skipped':tests['skipped'],'test_source_current':source_current,'eda_evidence':eda_path.relative_to(ROOT).as_posix(),'anomaly_evidence':anomaly_path.relative_to(ROOT).as_posix(),'local_reproduction_run':reproduction['run_id'],'local_reproduction_source_current':repro_source_match,'limitations':['No independent recipient/different-machine sign-off yet.','NASDAQ maps to XNYS in exchange_calendars; reference coverage only.','Hashes/metadata do not independently authenticate Yahoo prices.','Retrospective event context does not prove single causality.','Existing handed-off validation report predates expanded quality audit; supplementary quality evidence is separate.','TV2 preprocessing/model/training/web are outside this TV1 acceptance.'],'documentation_corrections':['Updated stale root/raw/metadata README statements.','Separated historical PR version from current snapshot statistics.','Added implemented TV1 code to implementation report.'],'resolved_findings':['Validation report write failure previously left partial outputs; added exclusive pair creation and rollback of owned outputs, verified by a new regression test.']}
    path=out/'summary.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    pointer={'summary':path.relative_to(ROOT).as_posix(),'dataset_version':version,'audit_run_id':stamp}
    (ROOT/'data/metadata/tv1_final_audit_latest.json').write_text(json.dumps(pointer,indent=2),encoding='utf-8')
    print(json.dumps({key:result[key] for key in ['audit_run_id','all_local_requirements_passed','fully_accepted','tests_run','conditional_items','artifacts_unchanged']},indent=2))
    if not all(checks):raise SystemExit(1)

if __name__=='__main__':main()
