"""Run from relocated payload; verify hashes/tests and recompute six-model comparison."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import site
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]


def main():
    manifest=json.loads((ROOT/'TV5_HANDOFF.json').read_text())
    for name,sha in manifest['files'].items():
        p=(ROOT/name).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
            raise ValueError('Payload mismatch '+name)
    import torch
    sys.path.insert(0,str(ROOT))
    from backend.models.cnn_one_step import CNNOneStep
    import inspect
    assert Path(inspect.getfile(CNNOneStep)).resolve().is_relative_to(ROOT)
    assert sys.prefix!=sys.base_prefix and site.ENABLE_USER_SITE is False and torch.version.cuda is None
    assert Path(torch.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    for line in (ROOT/'scripts/requirements-tv4-lock.txt').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            name,version=line.split('==');assert importlib.metadata.version(name)==version,(name,version)
    folder=ROOT/'logs/audit'/('tv5_handoff_verification_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
    env.pop('PYTHONPATH',None)
    cmd=[sys.executable,'-m','pytest','tests/models/test_cnn_one_step.py','tests/models/test_cnn_contract.py',
        'tests/models/test_cnn_learning.py','tests/training','tests/evaluation','-q','-p','no:cacheprovider',
        '--junitxml='+str(folder/'tests.xml')]
    run=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    (folder/'pytest.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
    assert run.returncode==0,run.stdout+run.stderr
    cases=list(ET.parse(folder/'tests.xml').getroot().iter('testcase'))
    assert len(cases)==162 and not any(c.tag in ('failure','error','skipped') for case in cases for c in case)
    receipts=[]
    for script in ['check_tv5_aapl_data.py','compare_tv5_validation.py','build_tv5_monitoring.py']:
        result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts'/script)],cwd=ROOT,env=env,
            capture_output=True,text=True,encoding='utf-8')
        assert result.returncode==0,result.stdout+result.stderr
        receipt=json.loads(result.stdout)
        evidence=json.loads(Path(receipt['evidence']).read_text())
        assert evidence['passed']
        receipts.append(receipt)
    summary=dict(passed=True,tests=len(cases),payload_files=len(manifest['files']),
        cnn_research_models=3,lstm_comparison_models=3,receipts=receipts,imports_from_relocated_root=True,
        clean_existing_environment=True,python=sys.version,trained_again=False,test_performance_evaluated=False,
        recipient_machine_verified=False)
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),tests=len(cases))))


if __name__=='__main__':main()
