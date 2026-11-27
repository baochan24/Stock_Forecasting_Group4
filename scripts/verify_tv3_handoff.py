"""Verify TV3 source/contract handoff; no trained checkpoint is advertised."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.validation.validator import compute_sha256


def notebook_source_digest(path):
    notebook=json.loads(Path(path).read_text(encoding='utf-8'))
    sources=[{'cell_type':c['cell_type'],'source':''.join(c['source']) if isinstance(c['source'],list) else c['source']} for c in notebook['cells']]
    return hashlib.sha256(json.dumps(sources,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()


def verify_members(root,manifest):
    root=Path(root).resolve()
    if manifest.get('format_version') != 1 or manifest.get('trained_checkpoints') != []:
        raise ValueError('Expected untrained source-only TV3 handoff contract')
    for mapping,hash_function in [(manifest['files'],compute_sha256),(manifest['notebook_sources'],notebook_source_digest)]:
        for relative,digest in mapping.items():
            path=(root/relative).resolve()
            if not path.is_relative_to(root) or hash_function(path) != digest: raise ValueError(f'Handoff checksum/path mismatch: {relative}')


def main():
    manifest=json.loads((ROOT/'HANDOFF_TV3.json').read_text(encoding='utf-8'))
    verify_members(ROOT,manifest)
    folder=ROOT/'logs/audit'/('tv3_handoff_verify_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True,exist_ok=False)
    common=['--dataset-version',manifest['dataset_version'],'--scaler-dir',manifest['scaler_relative'],'--prepared-dir',manifest['prepared_relative']]
    commands=[('tests',['scripts/run_tv3_checks.py','--require-clean']),('integration',['scripts/check_tv3_tv2.py',*common]),('trace',['scripts/check_tv3_trace.py',*common])]
    summary={'passed':False,'dataset_version':manifest['dataset_version'],'handoff_id':manifest['handoff_id'],'runs':{},
             'python':sys.executable,'trained_checkpoints':[],'recipient_machine_verified':False,'checkpoint_training_verified':False}
    env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
    env.pop('PYTHONPATH',None)
    try:
        for name,args in commands:
            run=subprocess.run([sys.executable,'-X','utf8',*args],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
            (folder/(name+'.log')).write_text(run.stdout+run.stderr,encoding='utf-8')
            if run.returncode: raise RuntimeError(f'{name} failed: {folder}')
            printed=json.loads(run.stdout)
            receipt=Path(printed['evidence'])
            summary['runs'][name]={'exit_code':0,'evidence':str(receipt)}
            (folder/(name+'_summary.json')).write_bytes(receipt.read_bytes())
            print(json.dumps({'stage':name,'passed':True}),flush=True)
        verify_members(ROOT,manifest)
        summary['passed']=True
    finally:
        (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'evidence':str(folder/'summary.json'),'runs':summary['runs']},indent=2))


if __name__=='__main__': main()
