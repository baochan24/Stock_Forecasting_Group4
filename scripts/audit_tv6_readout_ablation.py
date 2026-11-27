"""Reconcile paired readout ablation metrics, cohorts, checkpoints and history."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))


def main():
    folder=(ROOT/read(ROOT/'logs/audit/tv6_readout_ablation_latest.json')['evidence']).parent
    summary=read(folder/'summary.json')
    if not summary['passed'] or summary['test_forward'] or summary['promoted']:raise ValueError('Unexpected scope')
    expected={(y,s) for y in (2022,2023) for s in (42,123,456)}
    actual=[(r['validation_year'],r['seed']) for r in summary['runs']]
    if len(actual)!=6 or set(actual)!=expected:raise ValueError('Missing run')
    for name,sha in summary['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed source '+name)
    pred=pd.read_csv(folder/'predictions.csv',float_precision='round_trip')
    metrics=pd.read_csv(folder/'metrics.csv',float_precision='round_trip')
    protocol=read(ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json');version=protocol['semantic']['dataset_version']
    raw=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip').set_index('date').adjusted_close
    reference={}
    for values,g in pred.groupby(['validation_year','seed','readout','condition']):
        year,seed,readout,condition=values
        dates=raw.index.tolist();expected_keys=[(f'{version}:lb30:f1:{dates[i-1]}',d) for i,d in enumerate(dates) if i>=30 and d.startswith(str(year))]
        keys=list(zip(g.sample_id,g.target_date))
        if keys!=expected_keys:raise ValueError('Incomplete paired cohort')
        np.testing.assert_allclose(g.actual_price,[raw[d] for d in g.target_date],rtol=0,atol=1e-12)
        np.testing.assert_allclose(g.origin_price,[raw[d] for d in (k.rsplit(':',1)[-1] for k in g.sample_id)],rtol=0,atol=1e-12)
        score=metrics[(metrics.validation_year==year)&(metrics.seed==seed)&(metrics.readout==readout)&(metrics.condition==condition)]
        if len(score)!=1:raise ValueError('Metric count')
        e=(g.predicted_price-g.actual_price).tolist()
        np.testing.assert_allclose(score[['mae_usd','rmse_usd']].to_numpy()[0],
            [math.fsum(abs(v) for v in e)/len(e),math.sqrt(math.fsum(v*v for v in e)/len(e))],rtol=1e-12,atol=1e-12)
        if readout=='last':reference[(year,seed,condition)]=g
    if len(metrics)!=48 or len(reference)!=24:raise ValueError('Missing readout/condition metrics')
    for run in summary['runs']:
        path=ROOT/run['checkpoint'];manifest=read(path/'manifest.json')
        if manifest['readout']!='mean' or manifest['parameter_count']!=4513 or not manifest['reload_verified']:raise ValueError('Checkpoint config')
        if hashlib.sha256((path/'state_dict.pt').read_bytes()).hexdigest()!=manifest['checkpoint_sha256']:raise ValueError('Checkpoint checksum')
        log=pd.read_csv(folder/f'{run["validation_year"]}_mean_readout_seed{run["seed"]}'/'epoch_logs.csv',float_precision='round_trip')
        if int(log.loc[log.val_loss.idxmin(),'epoch'])!=manifest['best_epoch']:raise ValueError('Best epoch')
        scaler=read(ROOT/'artifacts/scalers'/manifest['scaler_id']/'scaler.json')
        row=metrics[(metrics.validation_year==run['validation_year'])&(metrics.seed==run['seed'])&(metrics.readout=='mean')&(metrics.condition=='real')].iloc[0]
        np.testing.assert_allclose(row.rmse_usd**2/scaler['scale'][0]**2,manifest['best_val_loss'],rtol=1e-10,atol=1e-12)
    report=dict(passed=True,runs_verified=6,metric_rows_verified=48,paired_prediction_rows=len(pred),
        full_cohorts_verified=True,best_epoch_checkpoint_verified=True,source_hashes_unchanged=True,test_forward=False,
        result_hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ['summary.json','metrics.csv','predictions.csv','gradient_log.csv']})
    (folder/'independent_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
