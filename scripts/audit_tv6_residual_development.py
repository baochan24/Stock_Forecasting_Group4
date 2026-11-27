"""Independent saved-results audit; no model forward or hyperparameter selection."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    pointer=json.loads((ROOT/'logs/audit/tv6_residual_development_latest.json').read_text())
    folder=(ROOT/pointer['evidence']).parent
    summary=json.loads((folder/'summary.json').read_text())
    if not summary['passed'] or summary['runs_completed']!=36 or summary['test_inference_performed']:
        raise ValueError('Incomplete or unexpected scope')
    plan=summary['plan']
    expected_runs={(year,task,rep,seed) for year in plan['validation_years'] for task in plan['tasks']
                   for rep in plan['representations'] for seed in plan['seeds']}
    actual_runs=[(r['validation_year'],r['task'],r['representation'],r['seed']) for r in summary['runs']]
    if len(actual_runs)!=len(set(actual_runs)) or set(actual_runs)!=expected_runs:
        raise ValueError('Missing, duplicate or extra experiment runs')
    for name,sha in summary['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed '+name)
    metrics=pd.read_csv(folder/'metrics.csv',float_precision='round_trip')
    aggregates=pd.read_csv(folder/'aggregates.csv',float_precision='round_trip')
    protocol=json.loads((ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json').read_text())
    version=protocol['semantic']['dataset_version']
    raw=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip').set_index('date').adjusted_close
    groups={}
    for run in summary['runs']:
        key=(run['validation_year'],run['task'])
        tag='residual' if run['representation'].startswith('origin-centered') else 'absolute'
        run_id=f'{key[0]}_{key[1]}_{tag}_seed{run["seed"]}'
        predictions=pd.read_csv(folder/run_id/'validation_predictions.csv',float_precision='round_trip')
        keys=list(zip(predictions.sample_id,predictions.target_date,predictions.horizon_step))
        if len(set(keys))!=len(keys):raise ValueError('Duplicate validation key')
        if key in groups and groups[key]!=keys:raise ValueError('Different paired cohorts')
        groups[key]=keys
        h=5 if key[1]=='lstm_h5' else 1
        dates=raw.index.tolist();expected=[]
        for i in range(29,len(dates)-h):
            future=dates[i+1:i+1+h]
            if all(day.startswith(str(key[0])) for day in future):
                sample=f'{version}:lb30:f{h}:{dates[i]}'
                expected.extend((sample,day,k+1) for k,day in enumerate(future))
        if keys!=expected:raise ValueError('Incomplete full-year validation coverage')
        if not predictions.target_date.str.startswith(str(key[0])).all():raise ValueError('Wrong validation year')
        np.testing.assert_allclose(predictions.actual_price,[raw[d] for d in predictions.target_date],rtol=0,atol=1e-12)
        np.testing.assert_allclose(predictions.baseline_price,[raw[d] for d in predictions.forecast_origin],rtol=0,atol=1e-12)
        selected=metrics[(metrics.validation_year==key[0])&(metrics.task==key[1])&
            (metrics.representation==run['representation'])&(metrics.seed==run['seed'])]
        for score in selected.itertuples():
            p=predictions if score.scope=='overall' else predictions[predictions.horizon_step==score.horizon_step]
            errors=(p.predicted_price-p.actual_price).tolist()
            np.testing.assert_allclose([score.mae_usd,score.rmse_usd],
                [math.fsum(abs(e) for e in errors)/len(errors),math.sqrt(math.fsum(e*e for e in errors)/len(errors))],rtol=1e-12,atol=1e-12)
        checkpoint=ROOT/run['checkpoint'];manifest=json.loads((checkpoint/'manifest.json').read_text())
        if manifest['purpose']!='post-test-development-not-release' or not manifest['reload_verified']:
            raise ValueError('Invalid checkpoint purpose')
        if hashlib.sha256((checkpoint/'state_dict.pt').read_bytes()).hexdigest()!=manifest['checkpoint_sha256']:
            raise ValueError('Checkpoint hash')
        history=pd.read_csv(folder/run_id/'epoch_logs.csv',float_precision='round_trip')
        if int(history.loc[history.val_loss.idxmin(),'epoch'])!=manifest['best_epoch']:raise ValueError('Wrong best epoch')
        fold=json.loads((folder/f'fold_{key[0]}_{key[1]}.json').read_text())
        fit=raw.loc[fold['scaler_fit']['fit_first_date']:fold['scaler_fit']['fit_last_date']]
        if fold['scaler_fit']['fit_last_date']>=f'{key[0]}-01-01' or fold['train_last_target']>=fold['validation_first_target']:
            raise ValueError('Fold leakage')
        scaler=json.loads((ROOT/'artifacts/scalers'/fold['scaler_id']/'scaler.json').read_text())
        np.testing.assert_allclose([scaler['mean'][0],scaler['var'][0]],[fit.mean(),fit.var(ddof=0)],rtol=1e-12,atol=1e-12)
        primary=selected if h==1 else selected[selected.scope=='overall']
        np.testing.assert_allclose(float(primary.rmse_usd.iloc[0])**2/scaler['scale'][0]**2,manifest['best_val_loss'],rtol=1e-10,atol=1e-12)
    for row in metrics[metrics.representation=='persistence'].itertuples():
        p=pd.read_csv(folder/f'{row.validation_year}_{row.task}_absolute_seed42'/'validation_predictions.csv',float_precision='round_trip')
        if row.scope!='overall':p=p[p.horizon_step==row.horizon_step]
        errors=(p.baseline_price-p.actual_price).tolist()
        np.testing.assert_allclose([row.mae_usd,row.rmse_usd],
            [math.fsum(abs(e) for e in errors)/len(errors),math.sqrt(math.fsum(e*e for e in errors)/len(errors))],rtol=1e-12,atol=1e-12)
    for row in aggregates.itertuples():
        g=metrics[(metrics.validation_year==row.validation_year)&(metrics.task==row.task)&
            (metrics.representation==row.representation)&(metrics.scope==row.scope)]
        if row.scope!='overall':g=g[g.horizon_step==row.horizon_step]
        if set(g.seed)!={42,123,456}:raise ValueError('Missing seeds')
        np.testing.assert_allclose([row.mae_mean,row.mae_std,row.rmse_mean,row.rmse_std],
            [statistics.mean(g.mae_usd),statistics.stdev(g.mae_usd),statistics.mean(g.rmse_usd),statistics.stdev(g.rmse_usd)],rtol=1e-12,atol=1e-12)
    result=dict(passed=True,runs_verified=36,paired_cohorts=len(groups),raw_actuals_verified=True,baseline_origin_verified=True,
        independent_metrics_and_aggregates=True,scaler_train_only_verified=True,checkpoint_hashes_and_best_epochs_verified=True,
        untouched_test_claim=False,test_inference_performed=False)
    result['result_hashes']={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ('metrics.csv','aggregates.csv','summary.json')}
    (folder/'independent_audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
