"""Last observed raw USD price, input only; no fitting."""
import numpy as np


def predict_persistence(input_values, forecast_length=1):
    x=np.asarray(input_values)
    if x.dtype.kind not in 'iuf' or x.ndim!=3 or x.shape[0]==0 or x.shape[1]==0 or x.shape[2]!=1:
        raise ValueError('Expected nonempty (B,T,1) numeric raw inputs')
    if not np.isfinite(x).all() or type(forecast_length) is not int or forecast_length not in (1,5):
        raise ValueError('Expected finite inputs and horizon 1 or 5')
    return np.repeat(x[:,-1,0:1].astype(np.float64),forecast_length,axis=1)
