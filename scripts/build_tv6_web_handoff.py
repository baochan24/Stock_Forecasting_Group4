"""Create a new local web runtime bundle, preserving locked release/artifacts."""
import hashlib,json,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.research_release import validate_release,REGISTRY
from backend.services.results.release_results import ReleaseResults


def main():
    release=validate_release(ROOT);sidecar=ReleaseResults(ROOT).validate(release)
    names=set(release['semantic']['files_sha256'])|set(sidecar['files_sha256'])
    names|={REGISTRY,'artifacts/releases/aapl-research-residual-v1/manifest.json',
        'experiments/configs/tv6_api_data_v1.registry.json','rule.md','FILE_STRUCTURE.md'}
    for folder,suffixes in [('backend',{'.py'}),('frontend',{'.js','.html','.css','.svg','.json','.md'}),('docs',{'.md'})]:
        for p in (ROOT/folder).rglob('*'):
            if folder=='docs' and not (p.name.startswith(('01_','02_','03_','04_','05_','06_','07_','08_','09_','10_','11_','12_','TV')) or p.name in ('đề_yêu_cầu.md','yêu_cầu_mẫu_đề_tài.md')):continue
            if p.is_file() and p.suffix in suffixes and not {'node_modules','__pycache__','.git'}&set(p.parts):names.add(p.relative_to(ROOT).as_posix())
    for p in (ROOT/'reports').glob('0[1-7]_*.md'):names.add(p.relative_to(ROOT).as_posix())
    for p in (ROOT/'reports/tables').glob('TV6_Final_*'):
        if p.is_file() and p.suffix in ('.csv','.json'):names.add(p.relative_to(ROOT).as_posix())
    names|={f'scripts/{p}' for p in ['requirements-tv4-lock.txt','requirements-tv6-api-lock.txt',
        'run_tv6_api.py','run_tv6_frontend.py','verify_tv6_web_handoff.py','check_tv6_frontend.mjs']}
    names|={'tests/api/test_tv6_api.py','tests/frontend/test_ui_contract.mjs','tests/integration/test_tv6_web_handoff.py'}
    # Preserve outputs for reading; full notebook Run All needs the research artifacts separately.
    names.add('notebooks/06_TV6_Integration_Evaluation_and_Demo.ipynb')
    for p in (ROOT/'reports/audits').glob('TV6_*.md'):names.add(p.relative_to(ROOT).as_posix())
    files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(names)}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive=ROOT/'artifacts/releases'/f'TV6_Web_Handoff_{stamp}.zip'
    manifest=dict(format_version=1,kind='local-web-runtime',release_id='aapl-research-residual-v1',
        release_sha256=release['semantic_sha256'],created_utc=stamp,files_sha256=files,
        notebook_mode='saved outputs; full research artifacts required for Run All',
        fresh_environment_verified=False,verified_on_other_machine=False,independent_holdout=False,
        redistribution_rights_verified=False,training=False,
        verification_note='Flags describe packaging time; later verification receipts are matched by the archive SHA-256.')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(names):z.write(ROOT/name,name)
        z.writestr('TV6_WEB_HANDOFF.json',json.dumps(manifest,indent=2))
        z.writestr('START_HERE.txt','Windows64/Python3.13.7. See docs/TV6_Member_Setup_and_Run.md.\n'
            'Create a new environment; pip install -r scripts/requirements-tv6-api-lock.txt.\n'
            'Run python scripts/verify_tv6_web_handoff.py, then run_tv6_api.py and run_tv6_frontend.py in separate terminals.\n'
            'This is a local runtime bundle; no .git, virtualenv, credentials, training or live data.\n'
            'Notebook contains saved outputs; full research Run All needs original audit logs/prepared artifacts.\n'
            'No public distribution rights or independent-machine acceptance is implied.\n')
    sha=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(sha+'  '+archive.name+'\n')
    result=dict(passed=True,zip=archive.relative_to(ROOT).as_posix(),sha256=sha,payload_files=len(files),bytes=archive.stat().st_size,
        release_sha256=release['semantic_sha256'],training=False,uploaded=False)
    (ROOT/'logs/audit/tv6_web_handoff_latest.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))


if __name__=='__main__':main()
