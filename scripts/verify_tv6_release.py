"""Smoke verify an extracted historical release; no training or fitting."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.research_release import validate_release
from backend.inference.release_forecaster import ReleaseForecaster


def main():
    document=validate_release(ROOT);s=document['semantic']
    engine=ReleaseForecaster(ROOT)
    frame=pd.read_csv(ROOT/s['snapshot'],float_precision='round_trip')
    dates=frame.date.tolist();prices=frame.adjusted_close.tolist();checks=[];all_rows=[]
    for h in (1,5):
        records=[]
        for origin in ('2023-06-15','2025-06-16'):
            i=dates.index(origin)
            records.append(dict(sample_id=f'{s["dataset_version"]}:lb30:f{h}:{origin}',dataset_version=s['dataset_version'],forecast_origin=origin,
                input_dates=dates[i-29:i+1],input_values=[[v] for v in prices[i-29:i+1]],lookback=30,forecast_length=h))
        for seed in (42,123,456):
            rows=engine.predict(records,methods=['lstm','cnn','persistence'] if h==1 else ['lstm','persistence'],seed=seed)
            if len(rows)!=len(records)*h*(3 if h==1 else 2):raise ValueError('Missing output rows')
            for r in rows:
                i=dates.index(r['forecast_origin'])
                if r['target_date']!=dates[i+r['horizon_step']] or not np.isfinite(r['predicted_price']):raise ValueError('Output contract')
                if r['method']=='persistence' and r['predicted_price']!=prices[i]:raise ValueError('Baseline contract')
            checks.append(dict(forecast_length=h,seed=seed,prediction_rows=len(rows),passed=True));all_rows.extend(rows)
    prediction_sha256=hashlib.sha256(json.dumps(all_rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    print(json.dumps(dict(passed=True,release_id=s['release_id'],source_root=str(ROOT),checks=checks,training=False,prediction_sha256=prediction_sha256)))


if __name__=='__main__':main()
