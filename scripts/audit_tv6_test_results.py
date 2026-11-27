"""Independent source/aggregate audit of the existing official test results; no forward."""
import hashlib
import json
from pathlib import Path
import statistics
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    pointer=json.loads((ROOT/'logs/audit/tv6_item5_latest.json').read_text())
    folder=(ROOT/pointer['evidence']).parent
    summary=json.loads((folder/'summary.json').read_text())
    ledger=json.loads((folder/'execution.json').read_text())
    if not summary['passed'] or ledger['status']!='completed':raise ValueError('Incomplete evaluation')
    for name,sha in summary['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed '+name)
    protocol=json.loads((ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json').read_text())
    version=protocol['semantic']['dataset_version']
    raw=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip').set_index('date').adjusted_close
    residuals=pd.read_csv(folder/'residuals.csv',float_precision='round_trip')
    np.testing.assert_allclose(residuals.actual_price,[raw[d] for d in residuals.target_date],rtol=0,atol=1e-12)
    baseline=residuals[residuals.method=='persistence']
    np.testing.assert_allclose(baseline.predicted_price,[raw[d] for d in baseline.forecast_origin],rtol=0,atol=1e-12)
    metrics=pd.read_csv(folder/'metrics.csv',float_precision='round_trip')
    aggregate=pd.read_csv(folder/'aggregates.csv',float_precision='round_trip')
    for row in aggregate.itertuples():
        g=metrics[(metrics.method==row.method)&(metrics.forecast_length==row.forecast_length)&(metrics.metric_scope==row.metric_scope)]
        if row.metric_scope!='overall':g=g[g.horizon_step==row.horizon_step]
        if set(g.seed)!={42,123,456}:raise ValueError('Missing seeds')
        for metric in ('mae_usd','rmse_usd'):
            values=g[metric].tolist()
            np.testing.assert_allclose([getattr(row,metric+'_mean'),getattr(row,metric+'_std')],
                [statistics.mean(values),statistics.stdev(values)],rtol=1e-12,atol=1e-12)
    audit=dict(passed=True,raw_actual_matches_snapshot=True,baseline_matches_origin=True,
        all_seed_aggregates_verified=True,residual_rows=len(residuals),aggregate_rows=len(aggregate),
        result_hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in
            ('test_predictions_usd.csv','metrics.csv','aggregates.csv','residuals.csv','execution.json','summary.json')})
    (folder/'independent_audit.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
