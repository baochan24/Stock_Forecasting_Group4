"""Run TV1 tests with explicit artifacts and save structured evidence and logs."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-version',required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.dataset_version):raise ValueError('Invalid dataset version')
    os.chdir(ROOT);sys.path.insert(0,str(ROOT))
    os.environ['TV1_DATASET_VERSION']=args.dataset_version
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'logs/audit'/f'tv1_tests_{stamp}';out.mkdir(parents=True,exist_ok=False)
    protected=[ROOT/f'data/raw/aapl_raw_{args.dataset_version}.csv',ROOT/f'data/metadata/aapl_metadata_{args.dataset_version}.json',ROOT/f'data/validated/aapl_validated_{args.dataset_version}.csv',ROOT/f'data/metadata/aapl_validation_report_{args.dataset_version}.json']
    def hashes():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    before=hashes()
    records=[]
    class Result(unittest.TextTestResult):
        def addSuccess(self,test):super().addSuccess(test);records.append({'test':test.id(),'status':'passed'})
        def addFailure(self,test,err):super().addFailure(test,err);records.append({'test':test.id(),'status':'failed'})
        def addError(self,test,err):super().addError(test,err);records.append({'test':test.id(),'status':'error'})
        def addSkip(self,test,reason):super().addSkip(test,reason);records.append({'test':test.id(),'status':'skipped','reason':reason})
        def addSubTest(self,test,subtest,err):
            super().addSubTest(test,subtest,err)
            if err is not None:records.append({'test':subtest.id(),'status':'subtest_failure'})
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/data'),pattern='test_*.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
    after=hashes()
    report={'run_id':stamp,'dataset_version':args.dataset_version,'passed':result.wasSuccessful() and not result.skipped and before==after,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'artifacts_unchanged':before==after,'artifact_hashes':after,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'dependencies':{name:importlib.metadata.version(name) for name in ['numpy','pandas','yfinance','exchange_calendars']},'records':records,'log_file':(out/'unittest.log').relative_to(ROOT).as_posix(),'recipient_verified':False,'scope':'TV1 only; synthetic offline pipeline plus actual local artifacts/handoff, not TV2 preprocessing or independent machine verification.'}
    (out/'unittest.log').write_text(stream.getvalue(),encoding='utf-8')
    report['unittest_log_sha256']=hashlib.sha256((out/'unittest.log').read_bytes()).hexdigest()
    report['source_hashes']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['backend/data','tests/data'] for p in sorted((ROOT/folder).rglob('*.py'))}
    (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(stream.getvalue());print('SUMMARY:',(out/'summary.json').relative_to(ROOT))
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
