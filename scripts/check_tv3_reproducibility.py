"""Run tests/integration/trace from a separate source+artifact copy, same machine."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.validation.validator import compute_sha256


def main():
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    copy_root=ROOT/'.venv'/('tv3_repro_'+run)
    copy_root.mkdir(parents=True,exist_ok=False)
    output=ROOT/'logs/audit'/('tv3_repro_'+run)
    output.mkdir(parents=True,exist_ok=False)
    files=set((ROOT/'backend/data').rglob('*.py'))
    for relative in ['backend/models/lstm_one_step','backend/models/lstm_multi_step','backend/model_trace','tests/models']:
        files.update((ROOT/relative).glob('*.py'))
    files.update(ROOT/p for p in ['backend/artifacts/scaler.py','backend/artifacts/prepared.py','backend/artifacts/lstm_checkpoint.py','backend/audit/tv2_leakage.py',
                                 'scripts/run_tv3_checks.py','scripts/check_tv3_tv2.py','scripts/check_tv3_trace.py','scripts/requirements-tv3-lock.txt'])
    version='aapl_2015_2025_acq_20261119T141302002415Z'
    scaler='artifacts/scalers/aapl_scaler_20261120T124720810874Z'
    prepared='data/prepared/tv2_prepared_20261122T145943242978Z'
    files.update(ROOT/p for p in [f'data/raw/aapl_raw_{version}.csv',f'data/validated/aapl_validated_{version}.csv'])
    files.update(ROOT/f'data/metadata/{prefix}_{version}.json' for prefix in ['aapl_metadata','aapl_validation_report','aapl_quality_audit'])
    files.update((ROOT/scaler).glob('*.json'))
    files.update(p for p in (ROOT/prepared).iterdir() if p.is_file())
    hashes={p.relative_to(ROOT).as_posix():compute_sha256(p) for p in files}
    for path in files:
        dest=copy_root/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dest)
    commands=[('tests',['scripts/run_tv3_checks.py','--require-clean']),
              ('integration',['scripts/check_tv3_tv2.py','--dataset-version',version,'--scaler-dir',scaler,'--prepared-dir',prepared]),
              ('trace',['scripts/check_tv3_trace.py','--dataset-version',version,'--scaler-dir',scaler,'--prepared-dir',prepared])]
    env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
    env.pop('PYTHONPATH',None)
    summary={'passed':False,'copied_root':str(copy_root),'python':sys.executable,'runs':{},'copied_hashes':hashes,
             'recipient_machine_verified':False,'scope':'Isolated source/artifact copy on the same local machine, no independent recipient verification.'}
    try:
        for name,args in commands:
            start=perf_counter()
            result=subprocess.run([sys.executable,'-X','utf8',*args],cwd=copy_root,env=env,capture_output=True,text=True,encoding='utf-8')
            (output/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
            summary['runs'][name]={'exit_code':result.returncode,'seconds':perf_counter()-start}
            if result.returncode: raise RuntimeError(f'{name} failed, see {output}')
            printed=json.loads(result.stdout)
            path=Path(printed['evidence'])
            shutil.copy2(path,output/(name+'_summary.json'))
            summary['runs'][name]['evidence']=str(path)
            print(json.dumps({'stage':name,'passed':True}),flush=True)
        for relative,digest in hashes.items():
            if compute_sha256(ROOT/relative) != digest or compute_sha256(copy_root/relative) != digest:
                raise AssertionError(f'Source/artifact changed: {relative}')
        summary['passed']=True
    finally:
        (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'evidence':str(output/'summary.json'),'runs':summary['runs']},indent=2))


if __name__=='__main__': main()
