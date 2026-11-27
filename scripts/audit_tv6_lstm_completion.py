"""Independent candidate closure audit and phase-labelled comparison table; no forward."""
import hashlib,json,math,statistics
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def main():
    folder=(ROOT/read(ROOT/'logs/audit/tv6_lstm_completion_latest.json')['evidence']).parent
    receipt=read(folder/'summary.json');config=read(ROOT/receipt['candidate_config'])
    if not receipt['passed'] or receipt['training_performed'] or receipt['refit_performed'] or receipt['independent_holdout']:
        raise ValueError('Unexpected closure scope')
    if digest(config['semantic'])!=config['semantic_sha256'] or config['semantic_sha256']!=receipt['candidate_sha256']:
        raise ValueError('Candidate semantic hash')
    if config['semantic']['evaluation_protocol']['independent_holdout'] or config['semantic']['stage']!='research-candidate-not-release':
        raise ValueError('Mislabelled evaluation')
    for name,sha in receipt['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed source '+name)
    predictions=pd.read_csv(folder/'predictions.csv',float_precision='round_trip')
    metrics=pd.read_csv(folder/'metrics.csv',float_precision='round_trip')
    aggregates=pd.read_csv(folder/'aggregates.csv',float_precision='round_trip')
    checks=pd.read_csv(folder/'pipeline_checks.csv')
    if len(checks)!=18 or not checks.weights_unchanged.all() or not checks.boundary_single_sample_matches.all():
        raise ValueError('Pipeline incomplete')
    protocol=read(ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json');version=protocol['semantic']['dataset_version']
    raw=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip').set_index('date').adjusted_close
    dates=raw.index.tolist()
    for (scope,h,method,seed),g in predictions.groupby(['scope','forecast_length','method','seed'],dropna=False):
        actual_keys=list(zip(g.sample_id,g.forecast_origin,g.target_date,g.horizon_step))
        expected=[]
        for i in range(29,len(dates)-h):
            future=dates[i+1:i+1+h]
            eligible=all(d.startswith(scope[-4:]) for d in future) if scope.startswith('development_') else all('2024-01-01'<=d<='2025-12-31' for d in future)
            if eligible:expected.extend((f'{version}:lb30:f{h}:{dates[i]}',dates[i],day,k+1) for k,day in enumerate(future))
        if actual_keys!=expected:raise ValueError('Incomplete cohort or order')
        np.testing.assert_allclose(g.actual_price,[raw[d] for d in g.target_date],rtol=0,atol=1e-12)
        np.testing.assert_allclose(g.origin_price,[raw[d] for d in g.forecast_origin],rtol=0,atol=1e-12)
        if method=='persistence':np.testing.assert_allclose(g.predicted_price,g.origin_price,rtol=0,atol=1e-12)
    for row in metrics.itertuples():
        g=predictions[(predictions.scope==row.scope)&(predictions.forecast_length==row.forecast_length)&(predictions.method==row.method)]
        if not pd.isna(row.seed):g=g[g.seed==row.seed]
        if row.metric_scope!='overall':g=g[g.horizon_step==row.horizon_step]
        errors=(g.predicted_price-g.actual_price).tolist()
        if len(errors)!=row.error_count or g.sample_id.nunique()!=row.sample_count:raise ValueError('Count mismatch')
        np.testing.assert_allclose([row.mae_usd,row.rmse_usd],
            [math.fsum(abs(e) for e in errors)/len(errors),math.sqrt(math.fsum(e*e for e in errors)/len(errors))],rtol=1e-12,atol=1e-12)
    for row in aggregates.itertuples():
        g=metrics[(metrics.scope==row.scope)&(metrics.forecast_length==row.forecast_length)&(metrics.method=='lstm_residual')&(metrics.metric_scope==row.metric_scope)]
        if row.metric_scope!='overall':g=g[g.horizon_step==row.horizon_step]
        if set(g.seed)!={42,123,456}:raise ValueError('Missing seeds')
        np.testing.assert_allclose([row.mae_mean,row.mae_std,row.rmse_mean,row.rmse_std],
            [statistics.mean(g.mae_usd),statistics.stdev(g.mae_usd),statistics.mean(g.rmse_usd),statistics.stdev(g.rmse_usd)],rtol=1e-12,atol=1e-12)
    # Consolidate existing evidence, explicitly retaining evaluation phase and period.
    comparison=[];evidence={}
    def append(frame,phase,label):
        primary=frame[(frame.forecast_length==1)|(frame.metric_scope=='overall')]
        for h,g in primary.groupby('forecast_length'):
            comparison.append(dict(model=label,phase=phase,forecast_length=h,seeds=g.seed.notna().sum(),
                mae_usd=float(g.mae_usd.mean()),rmse_usd=float(g.rmse_usd.mean()),
                sample_count=int(g.sample_count.iloc[0]) if 'sample_count' in g else None))
    for scope,g in metrics.groupby('scope'):
        append(g[g.method=='lstm_residual'],scope,'LSTM residual last')
        append(g[g.method=='persistence'],scope,'Persistence')
    for pointer,phase in [('tv6_item4_latest.json','original_validation_2023'),('tv6_item5_latest.json','original_test_2024_2025')]:
        path=(ROOT/read(ROOT/'logs/audit'/pointer)['evidence']).parent/'metrics.csv'
        evidence[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        old=pd.read_csv(path,float_precision='round_trip')
        append(old[old.method=='lstm'],phase,'LSTM v1 absolute')
    pd.DataFrame(comparison).to_csv(folder/'comparison.csv',index=False)
    result=dict(passed=True,candidate_models=6,pipeline_checks=18,metric_rows_verified=len(metrics),aggregate_rows_verified=len(aggregates),
        prediction_rows_verified=len(predictions),source_and_weight_hashes_unchanged=True,independent_holdout=False,
        comparison_source_hashes=evidence,result_hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in
            ['summary.json','execution.json','metrics.csv','aggregates.csv','predictions.csv','pipeline_checks.csv','comparison.csv']})
    (folder/'independent_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
