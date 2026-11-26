"""Strict same-order one-step USD comparison; no dropping or implicit joining."""
import numpy as np


def evaluate_one_step(actual, predicted, *, target_keys, prediction_keys):
    keys=list(target_keys)
    if not keys or len(set(keys))!=len(keys) or keys!=list(prediction_keys):
        raise ValueError('Expected unique identical ordered sample/date keys')
    a,p=np.asarray(actual),np.asarray(predicted)
    if a.shape!=(len(keys),1) or p.shape!=a.shape:
        raise ValueError('Expected matching (N,1) actual/predicted arrays')
    if a.dtype.kind not in 'iuf' or p.dtype.kind not in 'iuf' or not np.isfinite(a).all() or not np.isfinite(p).all():
        raise ValueError('Expected finite real USD prices')
    error=p.astype(np.float64)-a.astype(np.float64)
    return dict(sample_count=len(keys),mae_usd=float(np.abs(error).mean()),
                rmse_usd=float(np.sqrt(np.square(error).mean())))
