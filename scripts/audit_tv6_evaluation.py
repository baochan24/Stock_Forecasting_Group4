"""Independent validation-only raw-source/math/coverage audit; no model calls."""
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol


def main():
    protocol=json.loads((ROOT/PROTOCOL_PATH).read_text());sha=validate_protocol(protocol,ROOT)
    pointer=json.loads((ROOT/'logs/audit/tv6_item4_latest.json').read_text())
    path=ROOT/pointer['evidence'];receipt=json.loads(path.read_text())
    if not receipt['passed'] or receipt['test_performance_evaluated']:raise ValueError('Wrong evaluation scope')
    rows=pd.read_csv(path.parent/'residuals.csv',float_precision='round_trip')
    metrics=pd.read_csv(path.parent/'metrics.csv',float_precision='round_trip')
    aggregate=pd.read_csv(path.parent/'aggregates.csv',float_precision='round_trip')
    snapshot=pd.read_csv(ROOT/f"data/validated/aapl_validated_{protocol['semantic']['dataset_version']}.csv",float_precision='round_trip')
    prices=snapshot.set_index('date').adjusted_close
    np.testing.assert_allclose(rows.actual_price,[prices[d] for d in rows.target_date],rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(rows.error_usd,rows.predicted_price-rows.actual_price,rtol=1e-12,atol=1e-12)
    baseline=rows[rows.method=='persistence']
    np.testing.assert_allclose(baseline.predicted_price,[prices[d] for d in baseline.forecast_origin],rtol=1e-12,atol=1e-12)
    for m in metrics.itertuples():
        part=rows[(rows.method==m.method)&(rows.forecast_length==m.forecast_length)]
        if m.method!='persistence':part=part[part.seed==m.seed]
        if m.metric_scope!='overall':part=part[part.horizon_step==m.horizon_step]
        errors=part.predicted_price.to_numpy()-part.actual_price.to_numpy()
        mae=math.fsum(abs(float(e)) for e in errors)/len(errors)
        rmse=math.sqrt(math.fsum(float(e)*float(e) for e in errors)/len(errors))
        np.testing.assert_allclose([mae,rmse],[m.mae_usd,m.rmse_usd],rtol=1e-12,atol=1e-12)
        if len(errors)!=m.error_count or part.sample_id.nunique()!=m.sample_count:raise ValueError('Wrong counts')
    for a in aggregate.itertuples():
        part=metrics[(metrics.method==a.method)&(metrics.forecast_length==a.forecast_length)&(metrics.metric_scope==a.metric_scope)]
        if a.metric_scope!='overall':part=part[part.horizon_step==a.horizon_step]
        if sorted(part.seed.tolist())!=[42,123,456]:raise ValueError('Wrong seeds')
        for name in ('mae_usd','rmse_usd'):
            values=part[name].tolist()
            np.testing.assert_allclose([statistics.mean(values),statistics.stdev(values)],
                [getattr(a,name+'_mean'),getattr(a,name+'_std')],rtol=1e-12,atol=1e-12)
    validation_dates=snapshot.loc[snapshot.date.between('2023-01-01','2023-12-31'),'date'].tolist()
    coverage=[]
    for h in (1,5):
        n=len(validation_dates)-h+1
        part=rows[(rows.method=='lstm')&(rows.seed==42)&(rows.forecast_length==h)]
        for step in range(1,h+1):
            dates=part[part.horizon_step==step].target_date.tolist()
            expected=validation_dates[step-1:step-1+n]
            if dates!=expected:raise ValueError('Unexplained missing validation dates')
            coverage.append(dict(forecast_length=h,horizon_step=step,samples=len(dates),first_target=dates[0],last_target=dates[-1]))
    # Existing validation numbers must not change when only the guard is tightened.
    previous=pd.read_csv(ROOT/'logs/audit/tv6_item4_20261126T170304891907Z/metrics.csv',float_precision='round_trip')
    np.testing.assert_allclose(metrics[['mae_usd','rmse_usd']],previous[['mae_usd','rmse_usd']],rtol=1e-12,atol=1e-12)
    for name,expected in receipt['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Changed source/artifact')
    validate_protocol(protocol,ROOT)
    folder=ROOT/'logs/audit'/('tv6_evaluation_audit_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True)
    summary=dict(passed=True,metric_rows_verified=len(metrics),aggregate_rows_verified=len(aggregate),
        residual_rows_verified=len(rows),raw_actual_matches_snapshot=True,baseline_matches_origin_price=True,
        independent_math_matches=True,seed_std_matches=True,metrics_unchanged_after_guard_fix=True,
        coverage=coverage,excluded_h5_validation_target_starts=validation_dates[-4:],
        validation_cohorts=receipt['validation_cohorts'],test_performance_evaluated=False,
        source_evidence=path.relative_to(ROOT).as_posix(),protocol_sha256=sha,
        remaining=['held-out test2024-2025 remains item5','test error analysis remains item6',
            'adjusted-close point-in-time and unequal tuning-budget limits remain',
            'data2026/live/intraday/OHLCV are outside the frozen one-feature coursework scope'])
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (ROOT/'logs/audit/tv6_evaluation_audit_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),excluded_h5_starts=validation_dates[-4:])))


if __name__=='__main__':main()
