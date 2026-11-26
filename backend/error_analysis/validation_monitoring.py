"""Describe aligned validation errors, never select/tune models."""
import numpy as np
import pandas as pd
from backend.evaluation.one_step import evaluate_one_step


def analyze_validation_errors(frame, window=20, top_n=10):
    if type(window) is not int or window < 1 or type(top_n) is not int or top_n < 1:
        raise ValueError('Positive integer window/top_n required')
    required={'method','seed','sample_id','target_date','actual_usd','predicted_usd','error_usd'}
    if not required.issubset(frame.columns) or frame.empty:
        raise ValueError('Missing prediction columns or empty frame')
    rows=frame.copy(deep=True)
    summary=[];rolling=[];largest=[];monthly=[];reference=None;reference_actual=None
    for (method,seed), group in rows.groupby(['method','seed'],dropna=False,sort=False):
        dates=pd.to_datetime(group.target_date,format='%Y-%m-%d',errors='raise')
        if not dates.is_monotonic_increasing or dates.duplicated().any() or not (dates.dt.year==2023).all():
            raise ValueError('Expected ordered unique validation2023 dates')
        keys=list(zip(group.sample_id,group.target_date))
        actual=group.actual_usd.to_numpy(dtype=np.float64).reshape(-1,1)
        pred=group.predicted_usd.to_numpy(dtype=np.float64).reshape(-1,1)
        metric=evaluate_one_step(actual,pred,target_keys=keys,prediction_keys=keys)
        error=(pred-actual)[:,0]
        if not np.allclose(error,group.error_usd.to_numpy(),rtol=1e-12,atol=1e-12):
            raise ValueError('Stored residual differs from prediction minus actual')
        if reference is None: reference,reference_actual=keys,actual
        if keys!=reference or not np.array_equal(actual,reference_actual):
            raise ValueError('Methods must cover identical targets and actual values')
        seed=None if pd.isna(seed) else int(seed)
        common=dict(method=method,seed=seed)
        squared=np.square(error)
        summary.append(dict(**common,**metric,bias_usd=float(error.mean()),
            p95_abs_error_usd=float(np.quantile(np.abs(error),.95)),max_abs_error_usd=float(np.abs(error).max()),
            overprediction_fraction=float((error>0).mean()),
            top5_squared_error_share=float(np.sort(squared)[-5:].sum()/squared.sum()) if squared.sum() else 0.))
        for i in range(len(group)):
            value=np.nan
            if i+1>=window:
                subset=keys[i+1-window:i+1]
                value=evaluate_one_step(actual[i+1-window:i+1],pred[i+1-window:i+1],
                    target_keys=subset,prediction_keys=subset)['mae_usd']
            rolling.append(dict(**common,target_date=keys[i][1],rolling_mae_usd=value,window_sessions=window))
        ranked=group.assign(abs_error_usd=np.abs(error),squared_error_usd=squared).sort_values(
            ['abs_error_usd','target_date'],ascending=[False,True]).head(top_n)
        largest.extend(ranked.to_dict('records'))
        periods=dates.dt.strftime('%Y-%m').to_numpy()
        for month in sorted(set(periods)):
            mask=periods==month
            mkeys=[key for key,use in zip(keys,mask) if use]
            monthly.append(dict(**common,month=month,**evaluate_one_step(actual[mask],pred[mask],target_keys=mkeys,prediction_keys=mkeys)))
    return dict(summary=pd.DataFrame(summary),rolling=pd.DataFrame(rolling),
                largest=pd.DataFrame(largest),monthly=pd.DataFrame(monthly))
