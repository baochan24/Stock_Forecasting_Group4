"""Package TV3 source/contracts plus required TV2 inputs, never upload/train."""
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.validation.validator import compute_sha256
from verify_tv3_handoff import notebook_source_digest,verify_members


def main():
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    handoff_id='TV3_Handoff_'+run
    bundle=ROOT/'artifacts/releases'/handoff_id
    bundle.mkdir(parents=True,exist_ok=False)
    version='aapl_2015_2025_acq_20261119T141302002415Z'
    scaler='artifacts/scalers/aapl_scaler_20261120T124720810874Z'
    prepared='data/prepared/tv2_prepared_20261122T145943242978Z'
    files=set((ROOT/'backend/data').rglob('*.py'))
    for relative in ['backend/models/lstm_one_step','backend/models/lstm_multi_step','backend/model_trace','tests/models']:
        files.update((ROOT/relative).glob('*.py')); files.add(ROOT/relative/'README.md')
    files.update(ROOT/p for p in ['backend/artifacts/scaler.py','backend/artifacts/prepared.py','backend/artifacts/lstm_checkpoint.py','backend/audit/tv2_leakage.py'])
    for name in ['run_tv3_checks.py','check_tv3_tv2.py','check_tv3_trace.py','check_tv3_reproducibility.py','benchmark_tv3_precision.py',
                 'build_member_notebooks.py','execute_member_notebooks.py','package_tv3_handoff.py','verify_tv3_handoff.py','requirements-tv3-lock.txt']:
        files.add(ROOT/'scripts'/name)
    for name in ['rule.md','AGENTS.md','docs/01_Project_Description_and_Foundation.md','docs/02_System_Architecture.md','docs/03_Module_Boundaries.md',
                 'docs/04_Data_Flow_and_Contracts.md','docs/11_Decision_Log.md','docs/12_Team_Assignment.md',
                 'docs/05_API_Contract.md','docs/06_Technical_Risks.md','docs/08_Reproducibility_and_Release.md','docs/09_Setup_and_Run.md','docs/10_Open_Decisions.md',
                 'docs/đề_yêu_cầu.md','docs/yêu_cầu_mẫu_đề_tài.md','docs/TV2_Setup_and_Handoff.md',
                 'docs/TV3_Setup_and_Reproduce.md','docs/TV3_Trace_Contract.md','docs/TV3_Handoff_TV4_TV6.md',
                 'reports/audits/TV3_Progress.md','reports/audits/TV3_Environment_Reproduce.md','notebooks/README.md',
                 'notebooks/03_TV3_LSTM_Development_and_Tests.ipynb']:
        files.add(ROOT/name)
    files.update(ROOT/p for p in [f'data/raw/aapl_raw_{version}.csv',f'data/validated/aapl_validated_{version}.csv'])
    files.update(ROOT/f'data/metadata/{prefix}_{version}.json' for prefix in ['aapl_metadata','aapl_validation_report','aapl_quality_audit'])
    files.update((ROOT/scaler).glob('*.json'))
    files.update(p for p in (ROOT/prepared).iterdir() if p.is_file())
    files.add(ROOT/'logs/audit/tv3_precision_20261123T022251223682Z/summary.json')
    # Keep recent actual strict-clean test evidence matching current source.
    tests=[]
    for path in (ROOT/'logs/audit').glob('tv3_tests_*/summary.json'):
        value=json.loads(path.read_text(encoding='utf-8'))
        if value.get('passed') and value.get('require_clean') and all((ROOT/p).is_file() and compute_sha256(ROOT/p)==digest for p,digest in value.get('source_hashes',{}).items()):
            tests.append(path)
    if not tests: raise RuntimeError('Run current strict-clean tests before packaging')
    for name in ['summary.json','pytest.log','junit.xml','pip-check.log','requirements-freeze.txt']: files.add(max(tests).parent/name)
    for path in sorted(files):
        dest=bundle/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
    normal={p.relative_to(bundle).as_posix():compute_sha256(p) for p in bundle.rglob('*') if p.is_file() and p.suffix != '.ipynb'}
    notebooks={p.relative_to(bundle).as_posix():notebook_source_digest(p) for p in bundle.rglob('*.ipynb')}
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    status=subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True)
    manifest={'format_version':1,'handoff_id':handoff_id,'dataset_version':version,'scaler_relative':scaler,'prepared_relative':prepared,
              'model_dtype':'float64','model_configs':[{'model_class':'LSTMOneStep','hidden_size':32,'lookback':30,'forecast_length':1},
                                                      {'model_class':'LSTMMultiStep','hidden_size':32,'lookback':30,'forecast_length':5}],
              'trained_checkpoints':[],'recipient_machine_verified':False,'checkpoint_training_verified':False,
              'git_head':head.stdout.strip() if not head.returncode else None,'workspace_dirty':bool(status.stdout.strip()),
              'files':normal,'notebook_sources':notebooks,'scope':'TV3 source/contract handoff; no trained weights, no forecasting metrics.'}
    (bundle/'HANDOFF_TV3.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    verify_members(bundle,manifest)
    archive=bundle.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(bundle.rglob('*')):
            if path.is_file(): zipped.write(path,path.relative_to(bundle).as_posix())
    digest=compute_sha256(archive)
    with Path(str(archive)+'.sha256').open('x',encoding='utf-8') as stream: stream.write(f'{digest}  {archive.name}\n')
    folder=ROOT/'logs/audit'/('tv3_package_'+run); folder.mkdir(parents=True,exist_ok=False)
    summary={'passed':True,'handoff_id':handoff_id,'archive':str(archive),'archive_sha256':digest,'bundle_root':str(bundle),
             'files':len(normal),'notebooks':len(notebooks),'trained_checkpoints':[],'recipient_machine_verified':False,'uploaded':False}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({**summary,'evidence':str(folder/'summary.json')},indent=2))


if __name__=='__main__': main()
