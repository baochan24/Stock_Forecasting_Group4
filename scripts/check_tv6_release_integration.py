"""Full validation/test inference parity for the historical release, without training."""
from datetime import datetime,timezone
import hashlib,json,time
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from unittest.mock import patch
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.inference.release_forecaster import ReleaseForecaster
from backend.artifacts.research_release import validate_release

def read(p):return json.loads(p.read_text(encoding='utf-8'))


def main():
    release=validate_release(ROOT);engine=ReleaseForecaster(ROOT);semantic=release['semantic']
    protocol=read(ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json')
    completion=(ROOT/read(ROOT/'logs/audit/tv6_lstm_completion_latest.json')['evidence']).parent
    residual=pd.read_csv(completion/'predictions.csv',float_precision='round_trip')
    original={}
    for split,pointer,filename in [('val','tv6_item3_latest.json','validation_inference_usd.csv'),('test','tv6_item5_latest.json','test_predictions_usd.csv')]:
        source=(ROOT/read(ROOT/'logs/audit'/pointer)['evidence']).parent/filename
        original[split]=pd.read_csv(source,float_precision='round_trip')
    checks=[];output=[]
    with patch.object(StandardScaler,'fit',side_effect=RuntimeError('fit forbidden')),patch.object(StandardScaler,'partial_fit',side_effect=RuntimeError('partial_fit forbidden')):
        for split in ('val','test'):
            for h in (1,5):
                cohort=next(c for c in protocol['semantic']['cohorts'] if c['forecast_length']==h)
                inputs=read(ROOT/'data/prepared'/cohort['prepared_id']/f'f{h}_{split}_inputs.json')
                for seed in (42,123,456):
                    methods=['lstm','cnn'] if h==1 else ['lstm']
                    if seed==42:methods.append('persistence')
                    start=time.perf_counter();rows=engine.predict(inputs,methods=methods,seed=seed);seconds=time.perf_counter()-start
                    frame=pd.DataFrame(rows)
                    for method in methods:
                        selected=frame[frame.method==method]
                        if method=='lstm':
                            expected=residual[(residual.scope==('development_2023' if split=='val' else 'post_development_test_2024_2025'))&
                                (residual.forecast_length==h)&(residual.method=='lstm_residual')&(residual.seed==seed)]
                        else:
                            expected=original[split][(original[split].method==method)&(original[split].forecast_length==h)]
                            if method!='persistence':expected=expected[expected.seed==seed]
                        keys=['sample_id','forecast_origin','target_date','horizon_step']
                        if list(selected[keys].itertuples(index=False,name=None))!=list(expected[keys].itertuples(index=False,name=None)):
                            raise ValueError('Release keys differ from accepted evidence')
                        np.testing.assert_allclose(selected.predicted_price,expected.predicted_price,rtol=0,atol=1e-12)
                        if {'actual_price','error_usd','target_values'}&set(selected):raise ValueError('Targets in inference output')
                        checks.append(dict(split=split,forecast_length=h,seed=None if method=='persistence' else seed,method=method,
                            samples=len(inputs),prediction_rows=len(selected),tail_samples=len(inputs)%32,
                            max_abs_difference=float(np.max(np.abs(selected.predicted_price.to_numpy()-expected.predicted_price.to_numpy()))),request_seconds=seconds))
                    output.extend(rows)
    validate_release(ROOT)
    folder=ROOT/'logs/audit'/('tv6_item7_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    pd.DataFrame(checks).to_csv(folder/'checks.csv',index=False)
    pd.DataFrame(output).to_csv(folder/'release_predictions.csv',index=False)
    summary=dict(passed=True,release_id=semantic['release_id'],release_sha256=release['semantic_sha256'],models=9,
        method_mode_checks=len(checks),prediction_rows=len(output),fit_forbidden=True,training=False,weights_unchanged=True,
        matches_accepted_predictions=True,independent_holdout=False,api_implemented=False,frontend_implemented=False)
    (folder/'summary.json').write_text(json.dumps(summary,indent=2))
    (ROOT/'logs/audit/tv6_item7_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
    print(json.dumps(dict(**summary,evidence=str(folder/'summary.json'))))


if __name__=='__main__':main()
