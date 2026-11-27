"""Deep read-only handoff data check, including schema-only held-out targets."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.artifacts.scaler import load_scaler
from backend.artifacts.prepared import load_prepared_modes
from backend.audit.tv2_leakage import audit_train_statistics,audit_temporal_windows
from backend.data.transforms.scaling import inverse_scale


def main():
    inventory=json.loads((ROOT/'reports/audits/TV6_Input_Inventory.json').read_text())
    for name,digest in inventory['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    snapshot=load_tv1_snapshot(ROOT,inventory['dataset_version'])
    data=snapshot['data'];hashes=snapshot['acceptance']['hashes']
    assert hashes==inventory['source_hashes']
    prices=data.adjusted_close.to_numpy(dtype=np.float64)
    assert np.isfinite(prices).all() and (prices>0).all()
    scaler_id=inventory['models'][0]['scaler_id']
    scaler,sm=load_scaler(ROOT/'artifacts/scalers'/scaler_id,
        expected_dataset_version=inventory['dataset_version'],expected_source_hashes=hashes)
    stats=audit_train_statistics(data,scaler,sm['metadata'])
    rows=[];examples=[]
    prepared_ids=sorted({m['prepared_id'] for m in inventory['models']})
    for prepared_id in prepared_ids:
        modes,manifest=load_prepared_modes(ROOT/'data/prepared'/prepared_id,
            expected_dataset_version=inventory['dataset_version'],expected_source_hashes=hashes,
            expected_scaler_id=scaler_id,expected_lookback=30)
        for h,result in modes.items():
            audit=audit_temporal_windows(result,data,scaler)
            assert audit['passed']
            for ex in audit['hand_check_examples']:
                examples.append(dict(prepared_id=prepared_id,forecast_length=h,**ex))
            for split,batch in result['splits'].items():
                x,y=batch['X'],batch['y']
                assert x.dtype==y.dtype==np.float64
                assert np.isfinite(x).all() and np.isfinite(y).all()
                raw_x=np.stack([r['input_values'] for r in batch['inputs']])
                raw_y=np.stack([r['target_values'] for r in batch['targets']])
                np.testing.assert_allclose(inverse_scale(x,scaler),raw_x,rtol=1e-12,atol=1e-12)
                np.testing.assert_allclose(inverse_scale(y,scaler),raw_y,rtol=1e-12,atol=1e-12)
                assert len(set(r['sample_id'] for r in batch['inputs']))==len(x)
                rows.append(dict(prepared_id=prepared_id,forecast_length=h,split=split,
                    raw_window_samples=len(x),samples_if_common_history60=int((batch['target_indices']>=60).sum()),
                    first_origin=batch['inputs'][0]['forecast_origin'],first_target=batch['targets'][0]['target_dates'][0],
                    last_target=batch['targets'][-1]['target_dates'][-1],dtype=str(x.dtype),
                    cross_split_excluded=batch['excluded_cross_split_targets'],incomplete_excluded=batch['excluded_incomplete_targets']))
    # Compare exact bytes of data delivered in the previously verified ZIP.
    receipt=json.loads((ROOT/'logs/audit/tv5_item10_latest.json').read_text())
    archive=ROOT/receipt['zip']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['sha256']
    delivered=0
    with zipfile.ZipFile(archive) as z:
        payload=json.loads(z.read('TV5_HANDOFF.json'))
        for name,digest in inventory['files'].items():
            if name.startswith(('data/','artifacts/scalers/')):
                assert payload['files'][name]==digest
                assert hashlib.sha256(z.read(name)).hexdigest()==digest
                delivered+=1
    for model in inventory['models']:
        meta=json.loads((ROOT/model['checkpoint']/'manifest.json').read_text())['metadata']
        assert meta['dataset_version']==inventory['dataset_version'] and meta['source_hashes']==hashes
        assert meta['scaler_id']==scaler_id and meta['prepared_id']==model['prepared_id']
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in inventory['files'].items())
    folder=ROOT/'logs/audit'/('tv6_data_recheck_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(folder/'coverage.csv',index=False)
    (folder/'boundary_examples.json').write_text(json.dumps(examples,indent=2),encoding='utf-8')
    summary=dict(passed=True,snapshot_rows=len(data),first_date=data.date.iloc[0],last_date=data.date.iloc[-1],
        dataset_version=inventory['dataset_version'],scaler_id=scaler_id,prepared_ids=prepared_ids,
        scaler_train_statistics=stats,coverage=rows,models_provenance_verified=9,
        inventory_hashes_verified=len(inventory['files']),zip_data_files_verified=delivered,
        raw_prices_finite_positive=True,inverse_matches_raw=True,temporal_coverage_verified=True,
        files_unchanged=True,test_performance_evaluated=False,trained_again=False,
        source='Local frozen snapshot acceptance; no fresh Yahoo download or source authenticity claim')
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (ROOT/'logs/audit/tv6_data_recheck_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),zip_data_files=delivered)))


if __name__=='__main__':main()
