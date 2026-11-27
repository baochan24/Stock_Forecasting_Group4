"""Post-evaluation descriptions and input stress controls, never model selection."""
import numpy as np
import pandas as pd
from backend.evaluation.one_step import evaluate_one_step


def history_controls(raw,seed=20261127):
    x=np.asarray(raw,dtype=np.float64)
    if x.ndim!=3 or x.shape[1:]!=(30,1) or len(x)==0 or not np.isfinite(x).all() or (x<=0).any():
        raise ValueError('Expected positive finite (N,30,1) observed inputs')
    flat=np.repeat(x[:,-1:,:],30,axis=1)
    reverse=x.copy();reverse[:,:-1,:]=x[:,-2::-1,:]
    shuffle=x.copy();rng=np.random.default_rng(seed)
    for i in range(len(x)):shuffle[i,:-1,0]=x[i,rng.permutation(29),0]
    return dict(real=x.copy(),flat=flat,reverse_prefix=reverse,shuffle_prefix=shuffle)


def describe(group):
    required={'sample_id','target_date','horizon_step','predicted_price','actual_price','origin_price'}
    if group.empty or not required.issubset(group):raise ValueError('Missing diagnostic records')
    keys=list(zip(group.sample_id,group.target_date,group.horizon_step))
    actual=group.actual_price.to_numpy(dtype=np.float64).reshape(-1,1)
    predicted=group.predicted_price.to_numpy(dtype=np.float64).reshape(-1,1)
    origin=group.origin_price.to_numpy(dtype=np.float64).reshape(-1,1)
    metric=evaluate_one_step(actual,predicted,target_keys=keys,prediction_keys=keys)
    base=evaluate_one_step(actual,origin,target_keys=keys,prediction_keys=keys)
    error=(predicted-actual)[:,0];a=(predicted-origin)[:,0];delta=(actual-origin)[:,0]
    return dict(samples=group.sample_id.nunique(),error_count=len(group),mae_usd=metric['mae_usd'],rmse_usd=metric['rmse_usd'],
        baseline_mae_usd=base['mae_usd'],baseline_rmse_usd=base['rmse_usd'],bias_usd=float(error.mean()),
        underprediction_fraction=float((error<0).mean()),p95_abs_error_usd=float(np.quantile(np.abs(error),.95)),
        max_abs_error_usd=float(np.abs(error).max()),mean_adjustment_usd=float(a.mean()),
        std_adjustment_usd=float(a.std()),std_actual_change_usd=float(delta.std()),
        mean_abs_adjustment_usd=float(np.abs(a).mean()),
        mse_skill_vs_persistence=float(1-metric['rmse_usd']**2/base['rmse_usd']**2) if base['rmse_usd'] else None)


def summarize_errors(frame,thresholds,window=20,top_n=10):
    """Split by context/seed/horizon; subset metrics explicitly descriptive."""
    if type(window) is not int or window<1 or type(top_n) is not int or top_n<1:raise ValueError('Positive window/top_n')
    groups=['cohort','representation','method','seed','forecast_length']
    required=set(groups)|{'forecast_origin','sample_id','target_date','horizon_step','actual_price','predicted_price','origin_price'}
    if frame.empty or not required.issubset(frame):raise ValueError('Incomplete error context')
    summaries=[];months=[];years=[];tails=[];largest=[];rolling=[]
    for values,g in frame.groupby(groups,dropna=False,sort=False):
        context=dict(zip(groups,values));h=int(context['forecast_length'])
        for step in list(range(1,h+1))+([0] if h==5 else []):
            part=g if step==0 else g[g.horizon_step==step]
            c=dict(**context,horizon_step=None if step==0 else step,metric_scope='overall' if step==0 else 'per_horizon')
            summaries.append(dict(**c,**describe(part)))
            for month,p in part.groupby(part.target_date.str[:7]):months.append(dict(**c,month=month,**describe(p)))
            for year,p in part.groupby(part.target_date.str[:4]):years.append(dict(**c,year=year,**describe(p)))
            errors=(part.predicted_price-part.actual_price).abs()
            ranking=part.assign(abs_error_usd=errors).sort_values(['abs_error_usd','target_date','sample_id'],ascending=[False,True,True]).head(top_n)
            for _,row in ranking.iterrows():
                largest.append(dict(**c,sample_id=row.sample_id,forecast_origin=row.forecast_origin,target_date=row.target_date,
                    actual_price=row.actual_price,predicted_price=row.predicted_price,abs_error_usd=row.abs_error_usd,
                    actual_horizon_step=int(row.horizon_step)))
            mask=np.array([abs((r.actual_price-r.origin_price)/r.origin_price)>thresholds[int(r.horizon_step)] for r in part.itertuples()])
            for label,keep in [('train_p95_exceedance',mask),('within_train_p95',~mask)]:
                if keep.any():tails.append(dict(**c,stress_group=label,**describe(part.iloc[np.flatnonzero(keep)])))
            if step:
                p=part.sort_values('target_date')
                if p.target_date.duplicated().any():raise ValueError('Duplicate target date within horizon')
                actual=p.actual_price.to_numpy(dtype=np.float64).reshape(-1,1)
                predicted=p.predicted_price.to_numpy(dtype=np.float64).reshape(-1,1)
                origin=p.origin_price.to_numpy(dtype=np.float64).reshape(-1,1)
                keys=list(zip(p.sample_id,p.target_date,p.horizon_step))
                for end in range(window,len(p)+1):
                    sl=slice(end-window,end);subset=keys[sl]
                    score=evaluate_one_step(actual[sl],predicted[sl],target_keys=subset,prediction_keys=subset)
                    base=evaluate_one_step(actual[sl],origin[sl],target_keys=subset,prediction_keys=subset)
                    rolling.append(dict(**c,target_date=p.target_date.iloc[end-1],window_sessions=window,
                        mae_usd=score['mae_usd'],baseline_mae_usd=base['mae_usd']))
    return {n:pd.DataFrame(v) for n,v in dict(summary=summaries,monthly=months,yearly=years,stress=tails,largest=largest,rolling=rolling).items()}
