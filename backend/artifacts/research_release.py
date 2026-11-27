"""Integrity checks for a local historical research release; no model fitting."""
import hashlib,json
from pathlib import Path
from backend.audit.tv6_protocol import digest,resolve_member

REGISTRY='experiments/configs/tv6_research_release_v1.registry.json'
RELEASE_ID='aapl-research-residual-v1'


def file_hash(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_release(root,release_id=RELEASE_ID,*,registry_path=None):
    root=Path(root).resolve()
    registry=json.loads(resolve_member(root,registry_path or REGISTRY).read_text(encoding='utf-8'))
    if release_id!=RELEASE_ID or registry.get('release_id')!=release_id:raise ValueError('Unknown release ID')
    path=resolve_member(root,registry['manifest'])
    if file_hash(path)!=registry.get('manifest_sha256'):raise ValueError('Release manifest checksum mismatch')
    document=json.loads(path.read_text(encoding='utf-8'));s=document['semantic']
    if digest(s)!=document.get('semantic_sha256') or document['semantic_sha256']!=registry.get('semantic_sha256'):
        raise ValueError('Release semantic checksum mismatch')
    if (s['release_id']!=release_id or s['format_version']!=1 or s['kind']!='historical-research'
            or s['lookback']!=30 or s['dtype']!='float64' or s['torch_threads']!=1
            or s['demo_seed']!=42 or s['independent_holdout'] is not False):
        raise ValueError('Unsupported release contract')
    for name,expected in s['files_sha256'].items():
        if file_hash(resolve_member(root,name))!=expected:raise ValueError('Release file checksum mismatch: '+name)
    def pinned(name):
        if name not in s['files_sha256']:raise ValueError('Unpinned release member: '+name)
        return resolve_member(root,name)
    pinned(s['snapshot'])
    expected={('lstm',h,seed) for h in (1,5) for seed in (42,123,456)}|{('cnn',1,seed) for seed in (42,123,456)}
    keys=[]
    for entry in s['models']:
        key=(entry['method'],entry['forecast_length'],entry['seed']);keys.append(key)
        if type(entry['seed']) is not int or type(entry['forecast_length']) is not int:raise ValueError('Invalid model identity types')
        path=pinned(entry['checkpoint']+'/manifest.json')
        pinned(entry['checkpoint']+('/state_dict.pt' if entry['method']=='lstm' else '/weights.pt'))
        pinned('artifacts/scalers/'+entry['scaler_id']+'/manifest.json');pinned('artifacts/scalers/'+entry['scaler_id']+'/scaler.json')
        manifest=json.loads(path.read_text(encoding='utf-8'))
        if entry['method']=='lstm':
            if (entry['representation']!='origin-centered-price-delta-v1' or entry['readout']!='last'
                    or manifest['representation_version']!=entry['representation'] or manifest['seed']!=entry['seed']
                    or manifest['task']!=f'lstm_h{entry["forecast_length"]}' or manifest['validation_year']!=2023
                    or manifest['dataset_version']!=s['dataset_version'] or manifest['scaler_id']!=entry['scaler_id']
                    or manifest['best_epoch']!=entry['best_epoch']):raise ValueError('Residual checkpoint linkage mismatch')
            if manifest['checkpoint_sha256']!=s['files_sha256'][entry['checkpoint']+'/state_dict.pt']:raise ValueError('Residual state checksum linkage')
        elif entry['method']=='cnn':
            m=manifest['metadata']
            if (entry['representation']!='absolute-standardscaled-price-v1' or m['seed']!=entry['seed']
                    or m['run_id']!=entry['run_id'] or m['dataset_version']!=s['dataset_version']
                    or m['scaler_id']!=entry['scaler_id']):raise ValueError('CNN checkpoint linkage mismatch')
        else:raise ValueError('Unknown release method')
    if len(keys)!=9 or len(set(keys))!=9 or set(keys)!=expected:raise ValueError('Incomplete release catalog')
    return document
