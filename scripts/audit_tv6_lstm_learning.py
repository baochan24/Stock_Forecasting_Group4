"""Independent reconciliation of train-only references and gradient coverage."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))


def main():
    folder=(ROOT/read(ROOT/'logs/audit/tv6_lstm_learning_latest.json')['evidence']).parent
    summary=read(folder/'summary.json')
    if not summary['passed'] or summary['weight_updates'] or summary['test_inference']:raise ValueError('Unexpected scope')
    for name,sha in summary['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed source '+name)
    protocol=read(ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json')
    reference=read(folder/'train_references.json')
    for r in reference:
        h=r['forecast_length'];year=r['validation_year']
        cohort=next(c for c in protocol['semantic']['cohorts'] if c['forecast_length']==h)
        base=ROOT/'data/prepared'/cohort['prepared_id']
        xx=read(base/f'f{h}_train_inputs.json');yy=read(base/f'f{h}_train_targets.json')
        pairs=[(x,y) for x,y in zip(xx,yy) if all(d<=f'{year-1}-12-31' for d in y['target_dates'])]
        expected=[math.fsum(y['target_values'][k]-x['input_values'][-1][0] for x,y in pairs)/len(pairs) for k in range(h)]
        if len(pairs)!=r['train_samples'] or r['train_last_target']>=f'{year}-01-01':raise ValueError('Reference boundary')
        np.testing.assert_allclose(r['delta_usd'],expected,rtol=1e-12,atol=1e-12)
    predictions=pd.read_csv(folder/'reference_predictions.csv',float_precision='round_trip')
    metrics=pd.read_csv(folder/'reference_metrics.csv',float_precision='round_trip')
    # Actuals/origins and full cohorts independently from source ForecastInput/Target.
    for (year,h),part in predictions.groupby(['validation_year','forecast_length']):
        c=next(c for c in protocol['semantic']['cohorts'] if c['forecast_length']==h)
        base=ROOT/'data/prepared'/c['prepared_id'];split='train' if year==2022 else 'val'
        xx=read(base/f'f{h}_{split}_inputs.json');yy=read(base/f'f{h}_{split}_targets.json')
        pairs=[(x,y) for x,y in zip(xx,yy) if all(d.startswith(str(year)) for d in y['target_dates'])]
        keys=[(x['sample_id'],d,k+1) for x,y in pairs for k,d in enumerate(y['target_dates'])]
        actual=[v for x,y in pairs for v in y['target_values']]
        origin=[x['input_values'][-1][0] for x,y in pairs for k in range(h)]
        groups=list(part.groupby(['method','seed'],dropna=False))
        if len(groups)!=5:raise ValueError('Missing reference/model seeds')
        for (method,seed),g in groups:
            if list(zip(g.sample_id,g.target_date,g.horizon_step))!=keys:raise ValueError('Different cohort')
            np.testing.assert_allclose(g.actual_price,actual,rtol=0,atol=1e-12)
            np.testing.assert_allclose(g.origin_price,origin,rtol=0,atol=1e-12)
            if method=='persistence':np.testing.assert_array_equal(g.predicted_price,g.origin_price)
            if method=='train_mean_change':
                r=next(r for r in reference if r['validation_year']==year and r['forecast_length']==h)
                np.testing.assert_allclose(g.predicted_price-g.origin_price,[r['delta_usd'][k-1] for k in g.horizon_step],rtol=1e-12,atol=1e-12)
    for row in metrics.itertuples():
        p=predictions[(predictions.validation_year==row.validation_year)&(predictions.forecast_length==row.forecast_length)&(predictions.method==row.method)]
        if not pd.isna(row.seed):p=p[p.seed==row.seed]
        if row.metric_scope!='overall':p=p[p.horizon_step==row.horizon_step]
        if len(p)!=row.error_count:raise ValueError('Metric count')
        e=(p.predicted_price-p.actual_price).tolist()
        np.testing.assert_allclose([row.mae_usd,row.rmse_usd],[math.fsum(abs(v) for v in e)/len(e),math.sqrt(math.fsum(v*v for v in e)/len(e))],rtol=1e-12,atol=1e-12)
    gradients=pd.read_csv(folder/'gradient_norms.csv',float_precision='round_trip')
    groups=['validation_year','forecast_length','seed','state','batch']
    if len(gradients)!=108 or gradients.duplicated(groups).any():raise ValueError('Gradient coverage')
    zero=gradients[gradients.state=='reconstructed_zero_head_initialization']
    if not (zero.core_grad_l2==0).all() or not (zero.input_grad_l2==0).all():raise ValueError('Initial zero-head chain rule')
    values=gradients[['core_grad_l2','head_weight_grad_l2','head_bias_grad_l2','input_grad_l2']].to_numpy()
    if not np.isfinite(values).all() or (values<0).any():raise ValueError('Invalid gradient norms')
    result=dict(passed=True,train_references_verified=4,full_paired_cohorts_verified=4,metric_rows_verified=len(metrics),
        gradient_batches_verified=108,initial_zero_head_core_block_verified=True,source_artifacts_unchanged=True,
        result_hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in
            ['summary.json','train_references.json','reference_metrics.csv','reference_predictions.csv','gradient_norms.csv','input_gradient_by_session.csv','parameter_changes.csv']})
    (folder/'independent_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
