"""Independently reconcile item6 summaries/partitions/probes with saved sources."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=(ROOT/json.loads((ROOT/'logs/audit/tv6_item6_latest.json').read_text())['evidence']).parent
    summary=json.loads((folder/'summary.json').read_text())
    if not summary['passed'] or summary['models_probed']!=12 or summary['training_performed'] or summary['new_test_inference']:
        raise ValueError('Unexpected item6 scope')
    for name,sha in summary['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Source/artifact changed '+name)
    table=pd.read_csv(folder/'summary.csv',float_precision='round_trip')
    old=pd.read_csv(ROOT/summary['test_source']/'metrics.csv',float_precision='round_trip')
    official=table[table.cohort=='official_test_2024_2025']
    if len(official)!=len(old):raise ValueError('Missing official metrics')
    for row in official.itertuples():
        g=old[(old.method==row.method)&(old.forecast_length==row.forecast_length)&(old.metric_scope==row.metric_scope)]
        if not pd.isna(row.seed):g=g[g.seed==row.seed]
        if row.metric_scope!='overall':g=g[g.horizon_step==row.horizon_step]
        if len(g)!=1:raise ValueError('Ambiguous official row')
        np.testing.assert_allclose([row.mae_usd,row.rmse_usd],g[['mae_usd','rmse_usd']].to_numpy()[0],rtol=1e-12,atol=1e-12)
    monthly=pd.read_csv(folder/'monthly.csv');yearly=pd.read_csv(folder/'yearly.csv');stress=pd.read_csv(folder/'stress.csv')
    group=['cohort','representation','method','seed','forecast_length','horizon_step','metric_scope']
    def identity(frame):return frame[group].fillna('null').astype(str).agg('|'.join,axis=1)
    keys=identity(table)
    for name,parts in [('monthly',monthly),('yearly',yearly),('stress',stress)]:
        counts=parts.assign(identity=identity(parts)).groupby('identity').error_count.sum()
        for key,row in zip(keys,table.itertuples()):
            if counts.get(key)!=row.error_count:raise ValueError('Incomplete '+name+' partition')
    predictions=pd.read_csv(folder/'history_probe_predictions.csv',float_precision='round_trip')
    probes=pd.read_csv(folder/'history_probes.csv',float_precision='round_trip')
    for row in probes.itertuples():
        p=predictions[(predictions.validation_year==row.validation_year)&(predictions.forecast_length==row.forecast_length)&
            (predictions.seed==row.seed)&(predictions.control==row.control)]
        if row.metric_scope!='overall':p=p[p.horizon_step==row.horizon_step]
        if len(p)!=row.error_count or p.sample_id.nunique()!=row.samples:raise ValueError('Probe coverage')
        e=(p.predicted_price-p.actual_price).tolist()
        expected=[math.fsum(abs(v) for v in e)/len(e),math.sqrt(math.fsum(v*v for v in e)/len(e))]
        np.testing.assert_allclose([row.mae_usd,row.rmse_usd],expected,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(row.mean_abs_change_from_real_usd,(p.predicted_price-p.real_predicted_price).abs().mean(),rtol=1e-12,atol=1e-12)
        if row.control=='flat' and row.metric_scope!='overall':
            # Constant per-horizon correction, even though origin prices vary.
            correction=p.predicted_price-p.origin_price
            if correction.max()-correction.min()>1e-11:raise ValueError('Flat input not constant correction')
    baseline=table[(table.cohort=='official_test_2024_2025')&(table.method=='persistence')]
    np.testing.assert_allclose(baseline.mse_skill_vs_persistence,0,atol=1e-12)
    result=dict(passed=True,official_metric_rows_verified=len(official),summary_rows=len(table),
        partition_counts_verified=True,probe_metric_rows_verified=len(probes),probe_prediction_rows=len(predictions),
        flat_per_horizon_constant_verified=True,source_hashes_unchanged=True,training_performed=False,new_test_inference=False,
        result_hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in
            ['summary.json','summary.csv','monthly.csv','yearly.csv','stress.csv','largest.csv','rolling.csv','history_probes.csv','history_probe_predictions.csv','stress_thresholds.json']})
    (folder/'independent_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
