"""Full validation-only input/output acceptance for TV6 item3; no metrics."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.inference.frozen_forecaster import FrozenForecaster
from backend.data.transforms.scaling import inverse_scale


def main():
    engine=FrozenForecaster(ROOT)
    models=engine._protocol['semantic']['models']
    inventory=json.loads((ROOT/'reports/audits/TV6_Input_Inventory.json').read_text())
    watched=dict(inventory['files'])
    for name in ['backend/inference/frozen_forecaster.py','scripts/check_tv6_inference.py',
        'backend/baselines/persistence.py','backend/audit/tv6_protocol.py']:
        watched[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    output=[];checks=[]
    for h in (1,5):
        prepared_id=next(m['prepared_id'] for m in models if m['forecast_length']==h)
        folder=ROOT/'data/prepared'/prepared_id
        records=json.loads((folder/f'f{h}_val_inputs.json').read_text())
        target_metadata=json.loads((folder/f'f{h}_val_targets.json').read_text())
        with np.load(folder/f'f{h}_val.npz',allow_pickle=False) as arrays:
            stored_x=arrays['X'].copy()  # no target tensor loaded or metric calculated
        for seed in (42,123,456):
            methods=['lstm','cnn'] if h==1 else ['lstm']
            if seed==42:methods.append('persistence')
            rows=engine.predict(records,methods=methods,seed=seed)
            for method in methods:
                selected=[r for r in rows if r['method']==method]
                values=np.array([r['predicted_price'] for r in selected]).reshape(len(records),h)
                if method=='persistence':
                    expected=np.repeat([[r['input_values'][-1][0]] for r in records],h,axis=1)
                    np.testing.assert_array_equal(values,expected)
                else:
                    model=engine._cache[(method,h,seed)]
                    with torch.inference_mode():
                        direct=torch.cat([model(torch.from_numpy(stored_x[i:i+32])) for i in range(0,len(records),32)]).numpy()
                    expected=inverse_scale(direct,engine._scaler)
                    np.testing.assert_allclose(values,expected,rtol=1e-12,atol=1e-12)
                    if model.training or any(p.grad is not None or p.requires_grad for p in model.parameters()):
                        raise ValueError('Inference model is not frozen eval/no_grad')
                for i,(inp,target) in enumerate(zip(records,target_metadata)):
                    part=selected[i*h:(i+1)*h]
                    if ([r['sample_id'] for r in part]!=[inp['sample_id']]*h
                            or [r['target_date'] for r in part]!=target['target_dates']
                            or [r['horizon_step'] for r in part]!=list(range(1,h+1))):
                        raise ValueError('Output/date/sample/horizon alignment mismatch')
                checks.append(dict(method=method,forecast_length=h,seed=seed if method!='persistence' else None,
                    input_samples=len(records),output_rows=len(selected),tail_samples=len(records)%32,
                    max_abs_direct_difference=float(np.max(np.abs(values-expected))),
                    dates_match_prepared=True,finite_usd=bool(np.isfinite(values).all())))
            output.extend(rows)
    if len(output)!=6670 or len(engine._cache)!=9:raise ValueError('Missing models or output rows')
    for name,sha in watched.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('File changed: '+name)
    folder=ROOT/'logs/audit'/('tv6_item3_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    pd.DataFrame(output).to_csv(folder/'validation_inference_usd.csv',index=False)
    pd.DataFrame(checks).to_csv(folder/'checks.csv',index=False)
    summary=dict(passed=True,scope='validation2023 input-only inference acceptance',
        models=9,output_rows=len(output),method_mode_checks=len(checks),checks=checks,
        test_performance_evaluated=False,test_inference_enabled=False,metrics_calculated=False,
        trained_again=False,release_selected=False,protocol_sha256=engine._hash,
        source_artifacts_unchanged=True,source_hashes=watched,
        limitations=['Historical frozen validation scope only; no live quote or future calendar beyond snapshot',
            'release_id remains null until release integration; no API/frontend implementation'])
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (ROOT/'logs/audit/tv6_item3_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),models=9,output_rows=len(output))))


if __name__=='__main__':main()
