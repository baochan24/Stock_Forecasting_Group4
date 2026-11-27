"""Build a hash-bound read-only results sidecar; no inference or training."""
import json,shutil
from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.research_release import validate_release,file_hash,RELEASE_ID
from backend.audit.tv6_protocol import digest

REGISTRY='experiments/configs/tv6_api_data_v1.registry.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))


def main():
    release=validate_release(ROOT);s=release['semantic']
    source=(ROOT/read(ROOT/'logs/audit/tv6_item7_latest.json')['evidence']).parent
    acceptance=read(source/'acceptance.json')
    if not acceptance['passed'] or acceptance['release_sha256']!=release['semantic_sha256']:raise ValueError('Unaccepted release outputs')
    for name,sha in acceptance['evidence_hashes'].items():
        if file_hash(source/name)!=sha:raise ValueError('Changed release evidence')
    folder=ROOT/'artifacts/releases'/(RELEASE_ID+'-api-data')
    registry=ROOT/REGISTRY
    if registry.exists():
        doc=read(registry)
        if digest(doc['semantic'])!=doc['semantic_sha256']:raise ValueError('Sidecar changed')
        for name,sha in doc['semantic']['files_sha256'].items():
            if file_hash(ROOT/name)!=sha:raise ValueError('Sidecar member changed')
        print('Existing API sidecar verified');return
    folder.mkdir(parents=True,exist_ok=False)
    frame=pd.read_csv(source/'release_predictions.csv',float_precision='round_trip')
    if not (frame.release_id==RELEASE_ID).all() or not (frame.release_sha256==release['semantic_sha256']).all():raise ValueError('Mixed release outputs')
    raw=pd.read_csv(ROOT/s['snapshot'],float_precision='round_trip').set_index('date').adjusted_close
    frame['actual_price']=frame.target_date.map(raw)
    frame['error_usd']=frame.predicted_price-frame.actual_price
    frame['result_source']='stored_results'
    frame['evaluation_phase']=['validation_used_for_selection' if scope=='historical_validation' else
        ('post_development_old_test' if method=='lstm' else 'original_locked_test') for scope,method in zip(frame.scope,frame.method)]
    frame.to_csv(folder/'results.csv',index=False)
    experiments=[];files={}
    for entry in s['models']:
        cp=ROOT/entry['checkpoint'];manifest=read(cp/'manifest.json')
        if entry['method']=='lstm':
            h=ROOT/'logs/audit'/cp.parts[-2]/cp.name/'epoch_logs.csv';best=manifest['best_val_loss']
            config=dict(model=dict(input_size=1,hidden_size=32,output_size=entry['forecast_length']),training=dict(optimizer='adam',learning_rate=.001,batch_size=32,max_epochs=100,patience=10))
        else:
            h=cp.parent.parent/'runs'/entry['run_id']/'epoch_logs.csv';best=manifest['metadata']['best_val_loss']
            config=manifest['metadata']['training_config']
        dest=folder/'experiments'/entry['run_id'];dest.mkdir(parents=True)
        shutil.copyfile(h,dest/'history.csv')
        metadata=dict(run_id=entry['run_id'],method=entry['method'],forecast_length=entry['forecast_length'],seed=entry['seed'],
            dataset_version=s['dataset_version'],representation=entry['representation'],best_epoch=entry['best_epoch'],best_val_loss=best,
            configuration=config,checkpoint_selection='validation',training_source='archived',independent_holdout=False)
        (dest/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        experiments.append(dict(run_id=entry['run_id'],metadata=(dest/'metadata.json').relative_to(ROOT).as_posix(),history=(dest/'history.csv').relative_to(ROOT).as_posix()))
    for p in folder.rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=file_hash(p)
    semantic=dict(release_id=RELEASE_ID,release_sha256=release['semantic_sha256'],results=(folder/'results.csv').relative_to(ROOT).as_posix(),
        rows=len(frame),experiments=experiments,files_sha256=files,independent_holdout=False,
        evidence_id=source.name,acceptance_sha256=file_hash(source/'acceptance.json'))
    registry.write_text(json.dumps(dict(semantic=semantic,semantic_sha256=digest(semantic)),indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,rows=len(frame),experiments=len(experiments),registry=REGISTRY)))


if __name__=='__main__':main()
