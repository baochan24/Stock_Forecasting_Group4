"""Post-test descriptive diagnosis; reads saved predictions, never fits or forwards."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    import audit_tv6_test_results
    audit_tv6_test_results.main()
    pointer=json.loads((ROOT/'logs/audit/tv6_item5_latest.json').read_text())
    source=(ROOT/pointer['evidence']).parent
    summary=json.loads((source/'summary.json').read_text())
    protocol=json.loads((ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json').read_text())
    version=protocol['semantic']['dataset_version']
    raw=pd.read_csv(ROOT/f'data/validated/aapl_validated_{version}.csv',float_precision='round_trip').set_index('date').adjusted_close
    train=raw.loc[:'2022-12-31'];cap=float(train.max())
    distribution=[]
    for split,prices in [('train',train),('validation',raw.loc['2023-01-01':'2023-12-31']),('test',raw.loc['2024-01-01':])]:
        distribution.append(dict(split=split,rows=len(prices),minimum=prices.min(),maximum=prices.max(),mean=prices.mean(),
            fraction_prices_above_train_max=float((prices>cap).mean())))
    r=pd.read_csv(source/'residuals.csv',float_precision='round_trip')
    r['origin_price']=r.forecast_origin.map(raw)
    r['origin_above_train_max']=r.origin_price>cap
    r['year']=r.target_date.str[:4]
    r['seed_label']=r.seed.fillna(-1).astype(int)
    # Every row remains within its model/seed. Repeated seeds are not counted as independent sessions.
    rows=[]
    for (method,h,seed),g in r.groupby(['method','forecast_length','seed_label']):
        for name,part in [('all',g),('origin_within_train_max',g[~g.origin_above_train_max]),
                          ('origin_above_train_max',g[g.origin_above_train_max])]+[(year,g[g.year==year]) for year in ('2024','2025')]:
            if part.empty:continue
            error=part.predicted_price-part.actual_price
            baseline_error=part.origin_price-part.actual_price
            shift=part.predicted_price-part.origin_price
            rows.append(dict(method=method,forecast_length=h,seed=seed,segment=name,
                samples=part.sample_id.nunique(),error_count=len(part),mae=error.abs().mean(),rmse=np.sqrt((error**2).mean()),
                bias=error.mean(),underprediction_fraction=(error<0).mean(),
                baseline_mae_same_rows=baseline_error.abs().mean(),
                mean_predicted_change=shift.mean(),mean_actual_change=(part.actual_price-part.origin_price).mean(),
                persistence_mse=(baseline_error**2).mean(),model_adjustment_mse=(shift**2).mean(),
                minus_twice_adjustment_actual_change=-2*(shift*(part.actual_price-part.origin_price)).mean()))
    folder=source/'gap_diagnosis';folder.mkdir(exist_ok=True)
    pd.DataFrame(distribution).to_csv(folder/'price_distribution.csv',index=False)
    table=pd.DataFrame(rows);table.to_csv(folder/'diagnosis_by_seed.csv',index=False)
    for row in rows:
        np.testing.assert_allclose(row['rmse']**2,row['persistence_mse']+row['model_adjustment_mse']+row['minus_twice_adjustment_actual_change'],rtol=1e-12,atol=1e-12)
    receipt=dict(passed=True,scope='post-test descriptive diagnosis, not causal proof',
        source_evidence=pointer['evidence'],protocol_sha256=summary['protocol_sha256'],train_max=cap,
        test_h1_sessions=502,test_h1_origins_above_train_max=int(r[(r.forecast_length==1)&(r.method=='persistence')].origin_above_train_max.sum()),
        exact_mse_decomposition_verified=True,trained=False,new_inference=False,tuned=False,
        limitations=['Price-level association does not isolate causal effects from trend, volatility or window history',
            'Train online loss and validation eval loss are not directly comparable frozen-model risks',
            'No gate saturation measurement or claim; no residual-target ablation performed'])
    (folder/'summary.json').write_text(json.dumps(receipt,indent=2))
    print(pd.DataFrame(distribution).to_string(index=False))
    print(table[(table.forecast_length==1)&(table.segment=='all')].to_string(index=False))
    print(folder)


if __name__=='__main__':main()
