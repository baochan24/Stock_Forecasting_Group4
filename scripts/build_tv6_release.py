"""Create an immutable local release and portable ZIP from accepted existing models."""
import argparse,json,hashlib,zipfile
from datetime import datetime,timezone
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol,digest
from backend.artifacts.research_release import RELEASE_ID,REGISTRY,file_hash,validate_release


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main(draft=False):
    protocol=read(ROOT/PROTOCOL_PATH);validate_protocol(protocol,ROOT)
    candidate_path='experiments/configs/tv6_lstm_residual_candidate_v1.json';candidate=read(ROOT/candidate_path)
    if digest(candidate['semantic'])!=candidate['semantic_sha256']:raise ValueError('Candidate fingerprint')
    completion=(ROOT/read(ROOT/'logs/audit/tv6_lstm_completion_latest.json')['evidence']).parent
    receipt=read(completion/'summary.json');audit=read(completion/'independent_audit.json')
    if not receipt['passed'] or not audit['passed'] or receipt['candidate_sha256']!=candidate['semantic_sha256']:raise ValueError('Candidate not accepted')
    for name,sha in receipt['source_hashes'].items():
        if file_hash(ROOT/name)!=sha:raise ValueError('Candidate source changed '+name)
    for name,sha in audit['result_hashes'].items():
        if file_hash(completion/name)!=sha:raise ValueError('Candidate result changed')
    inventory=read(ROOT/'reports/audits/TV6_Input_Inventory.json')
    models=[];names=set()
    for e in candidate['semantic']['models']:
        models.append(dict(**e,method='lstm',run_id=Path(e['checkpoint']).name,representation=candidate['semantic']['representation']))
    for e in protocol['semantic']['models']:
        if e['method'].lower()=='cnn':models.append(dict(method='cnn',forecast_length=1,seed=e['seed'],checkpoint=e['checkpoint'],
            scaler_id=e['scaler_id'],run_id=e['run_id'],best_epoch=e['best_epoch'],representation='absolute-standardscaled-price-v1',readout='cnn'))
    for e in models:
        weights='state_dict.pt' if e['method']=='lstm' else 'weights.pt'
        for name in [e['checkpoint']+'/manifest.json',e['checkpoint']+'/'+weights,'artifacts/scalers/'+e['scaler_id']+'/manifest.json','artifacts/scalers/'+e['scaler_id']+'/scaler.json']:
            if not (ROOT/name).is_file():raise FileNotFoundError(name)
            names.add(name)
    snapshot=f'data/validated/aapl_validated_{inventory["dataset_version"]}.csv'
    names.update([snapshot,candidate_path,PROTOCOL_PATH,'scripts/requirements-tv4-lock.txt','scripts/verify_tv6_release.py'])
    # Package source required for local reproducibility; no environments, raw acquisition, notebooks or logs.
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'backend').rglob('*.py') if '__pycache__' not in p.parts)
    files={name:file_hash(ROOT/name) for name in sorted(names)}
    semantic=dict(format_version=1,release_id=RELEASE_ID,kind='historical-research',dataset_version=inventory['dataset_version'],
        source_hashes=inventory['source_hashes'],snapshot=snapshot,lookback=30,dtype='float64',torch_threads=1,demo_seed=42,
        independent_holdout=False,models=models,files_sha256=files,candidate_sha256=candidate['semantic_sha256'],
        evidence=dict(candidate=receipt['candidate_config'],completion_audit_sha256=file_hash(completion/'independent_audit.json')),
        policy=dict(allowed_target_splits=['val','test'],h5_requires_same_split=True,live_data=False,training=False),
        limitations=['Historical adjusted AAPL prices, retrospective adjustment; not point-in-time.',
            'Residual developed after observing old test; small baseline advantage is not independent proof.',
            'Research demonstration; no trading profitability claim.'])
    document=dict(semantic=semantic,semantic_sha256=digest(semantic))
    release_dir=ROOT/'logs/audit'/('tv6_release_draft_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')) if draft else ROOT/'artifacts/releases'/RELEASE_ID
    manifest=release_dir/'manifest.json';registry=release_dir/'registry.json' if draft else ROOT/REGISTRY
    registry_name=registry.relative_to(ROOT).as_posix()
    if manifest.exists() or registry.exists():
        if not manifest.exists() or not registry.exists() or read(manifest)!=document:raise ValueError('Release exists or source changed; refusing overwrite')
        validate_release(ROOT,registry_path=registry_name);print('Existing release verified');return
    release_dir.mkdir(parents=True,exist_ok=False)
    manifest.write_text(json.dumps(document,indent=2),encoding='utf-8')
    registry.write_text(json.dumps(dict(release_id=RELEASE_ID,manifest=manifest.relative_to(ROOT).as_posix(),
        manifest_sha256=file_hash(manifest),semantic_sha256=document['semantic_sha256']),indent=2),encoding='utf-8')
    validate_release(ROOT,registry_path=registry_name)
    if draft:
        print(json.dumps(dict(passed=True,draft=True,registry=registry_name,models=len(models))));return
    archive=ROOT/'artifacts/releases'/(RELEASE_ID+'.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(names|{manifest.relative_to(ROOT).as_posix(),REGISTRY}):z.write(ROOT/name,name)
        z.writestr('RELEASE_README.txt','Historical AAPL research release. No training required.\n'
            'Use Python3.13 with scripts/requirements-tv4-lock.txt; run python scripts/verify_tv6_release.py.\n'
            'LSTM uses residual decode, CNN uses absolute inverse scaling; ReleaseForecaster chooses correctly.\n'
            'Default seed42, all3seeds preserved. Historical2023-2025 only, no live prices.\n'
            'Old test was observed before residual development; not independent held-out proof.\n')
    print(json.dumps(dict(passed=True,release_id=RELEASE_ID,models=len(models),payload_files=len(files),zip=str(archive),zip_sha256=file_hash(archive))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--draft',action='store_true')
    main(draft=parser.parse_args().draft)
