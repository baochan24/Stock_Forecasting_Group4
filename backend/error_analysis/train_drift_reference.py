"""Train-only mean price-change reference for development diagnosis, not release."""
from datetime import date
import numpy as np


def estimate_train_change(inputs,targets,*,dataset_version,train_last_date):
    date.fromisoformat(train_last_date)
    if not inputs or len(inputs)!=len(targets):raise ValueError('Nonempty paired training records required')
    h=inputs[0]['forecast_length'];deltas=[];days=[];seen=set()
    if type(h) is not int or h not in (1,5):raise ValueError('Expected forecast length 1 or 5')
    for x,y in zip(inputs,targets):
        if x['sample_id']!=y['sample_id'] or x['sample_id'] in seen:raise ValueError('Pair mismatch/duplicate')
        seen.add(x['sample_id'])
        if x['dataset_version']!=dataset_version or x['forecast_length']!=h or y['split']!='train':
            raise ValueError('Expected same-version training-only source')
        target_days=y['target_dates']
        if len(target_days)!=h or target_days!=sorted(set(target_days)):raise ValueError('Invalid target dates')
        if any(date.fromisoformat(d).isoformat()!=d for d in target_days):raise ValueError('Noncanonical date')
        if not x['forecast_origin']<target_days[0] or target_days[-1]>train_last_date:
            raise ValueError('Target beyond training cutoff or before origin')
        raw=np.asarray(x['input_values'],dtype=np.float64);target=np.asarray(y['target_values'],dtype=np.float64)
        if raw.shape!=(30,1) or target.shape!=(h,) or not np.isfinite(raw).all() or not np.isfinite(target).all():
            raise ValueError('Invalid training price shape/finite values')
        if (raw<=0).any() or (target<=0).any():raise ValueError('Expected positive prices')
        deltas.append(target-raw[-1,0]);days.extend(target_days)
    delta=np.stack(deltas).mean(axis=0)
    return dict(reference_version='train-mean-price-change-v1',dataset_version=dataset_version,forecast_length=h,
        delta_usd=delta.tolist(),train_samples=len(inputs),train_first_target=min(days),train_last_target=max(days),
        train_cutoff=train_last_date,purpose='development-diagnostic-not-release')


def predict_train_change(raw_inputs,reference):
    raw=np.asarray(raw_inputs,dtype=np.float64)
    delta=np.asarray(reference['delta_usd'],dtype=np.float64)
    if raw.ndim!=3 or raw.shape[1:]!=(30,1) or len(raw)==0 or not np.isfinite(raw).all() or (raw<=0).any():
        raise ValueError('Expected positive finite input history')
    h=reference['forecast_length']
    if type(h) is not int or h not in (1,5) or delta.shape!=(h,) or not np.isfinite(delta).all():
        raise ValueError('Invalid reference shape/values')
    output=raw[:,-1,0,None]+delta[None,:]
    if not np.isfinite(output).all():raise ValueError('Nonfinite reference prediction')
    return output
