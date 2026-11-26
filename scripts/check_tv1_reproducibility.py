"""Reproduce TV1 in a separate workspace using an explicitly supplied clean Python."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python',required=True)
    parser.add_argument('--dataset-version',required=True)
    args=parser.parse_args()
    clean_python=Path(args.python).resolve()
    if not clean_python.is_file():raise FileNotFoundError(clean_python)
    # Import the verifier from the source project, without introducing dependency paths.
    sys.path.insert(0,str(ROOT))
    from scripts.verify_tv1_handoff import verify
    version=args.dataset_version
    if not version or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in version):raise ValueError('Invalid version')
    receipt_path=ROOT/f'data/metadata/aapl_handoff_{version}_complete.json'
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    archive=ROOT/receipt['archive'];checksum=archive.with_suffix('.zip.sha256')
    verified=verify(archive,checksum)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    workspace=ROOT/'.venv'/f'tv1_repro_{stamp}'
    workspace.mkdir(parents=True,exist_ok=False)
    evidence=ROOT/'logs/audit'/f'tv1_repro_{stamp}';evidence.mkdir(parents=True,exist_ok=False)
    source_hashes={}
    for folder in ['backend/data','tests/data','scripts','docs','notebooks']:
        for source in (ROOT/folder).rglob('*'):
            if not source.is_file() or source.suffix not in ['.py','.md','.txt','.ipynb'] or '__pycache__' in source.parts:continue
            relative=source.relative_to(ROOT);target=workspace/relative
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            source_hashes[relative.as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
    audit_folder=workspace/'reports/audits';audit_folder.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'reports/audits/TV1_Anomaly_Sources.json',audit_folder/'TV1_Anomaly_Sources.json')
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            if name.startswith('data/'):
                target=workspace/name;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(bundle.read(name))
    for source in [archive,checksum,receipt_path]:
        target=workspace/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    env['PYTHONNOUSERSITE']='1';env['TV1_NOTEBOOK_PYTHON']=str(clean_python);env['PYTHONIOENCODING']='utf-8'
    def run(label,command):
        result=subprocess.run(command,cwd=workspace,env=env,text=True,encoding='utf-8',errors='replace',capture_output=True)
        (evidence/f'{label}.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError(f'{label} failed; see {evidence}')
        return result.stdout
    config=json.loads(run('environment',[str(clean_python),'-c',"import json,sys,site;from pathlib import Path;print(json.dumps({'python':sys.executable,'version':sys.version,'user_site_enabled':site.ENABLE_USER_SITE,'pyvenv_config':(Path(sys.prefix)/'pyvenv.cfg').read_text()}))"]))
    if config['user_site_enabled'] or 'include-system-site-packages = false' not in config['pyvenv_config']:raise ValueError('Python environment is not isolated')
    run('pip_check',[str(clean_python),'-m','pip','check'])
    freeze=run('pip_freeze',[str(clean_python),'-m','pip','freeze'])
    (evidence/'requirements-freeze.txt').write_text(freeze,encoding='utf-8')
    run('tests',[str(clean_python),'scripts/run_tv1_checks.py','--dataset-version',version])
    test_path=sorted((workspace/'logs/audit').glob('tv1_tests_*/summary.json'))[-1]
    tests=json.loads(test_path.read_text(encoding='utf-8'))
    run('notebook',[str(clean_python),'scripts/execute_data_exploration.py'])
    nb=json.loads((workspace/'notebooks/01_AAPL_Data_Exploration.ipynb').read_text(encoding='utf-8'))
    cells=[c for c in nb['cells'] if c['cell_type']=='code']
    notebook_passed=all(c.get('execution_count') is not None for c in cells) and not any(o['output_type']=='error' for c in cells for o in c.get('outputs',[]))
    for relative,digest in tests['artifact_hashes'].items():
        if hashlib.sha256((workspace/relative).read_bytes()).hexdigest()!=digest:raise ValueError('Reproduction modified dataset')
    result={'run_id':stamp,'dataset_version':version,'passed':tests['passed'] and notebook_passed,'same_machine_only':True,'independent_recipient_verified':False,'clean_environment':config,'workspace':workspace.relative_to(ROOT).as_posix(),'archive_verification':verified,'tests_run':tests['tests_run'],'test_summary':str(test_path.relative_to(ROOT)),'notebook_code_cells':len(cells),'notebook_passed':notebook_passed,'source_hashes':source_hashes,'evidence_folder':evidence.relative_to(ROOT).as_posix(),'requirements_freeze':(evidence/'requirements-freeze.txt').relative_to(ROOT).as_posix()}
    (evidence/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data/metadata/tv1_reproducibility_latest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['run_id','passed','tests_run','notebook_passed','same_machine_only','evidence_folder']},indent=2))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
