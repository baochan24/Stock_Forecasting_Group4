"""Versioned residual-price representation; no fitting or target access at inference."""
import numpy as np

REPRESENTATION='origin-centered-price-delta-v1'


def _scale(value):
    if isinstance(value,bool) or not np.isscalar(value) or not np.isfinite(value) or value<=0:
        raise ValueError('Expected positive finite training price scale')
    return float(value)


def encode_history(raw_inputs,training_scale):
    x=np.asarray(raw_inputs,dtype=np.float64)
    if x.ndim!=3 or x.shape[1:]!=(30,1) or len(x)==0 or not np.isfinite(x).all() or (x<=0).any():
        raise ValueError('Expected finite positive price history (B,30,1)')
    anchor=x[:,-1,0].copy()
    return (x-anchor[:,None,None])/_scale(training_scale),anchor


def encode_targets(raw_targets,anchor,training_scale):
    y=np.asarray(raw_targets,dtype=np.float64);a=np.asarray(anchor,dtype=np.float64)
    if y.ndim!=2 or y.shape[1] not in (1,5) or a.shape!=(len(y),) or len(y)==0:
        raise ValueError('Invalid residual target/anchor shapes')
    if not np.isfinite(y).all() or not np.isfinite(a).all() or (y<=0).any() or (a<=0).any():
        raise ValueError('Expected positive finite targets and anchors')
    return (y-a[:,None])/_scale(training_scale)


def decode_prices(scaled_deltas,anchor,training_scale):
    y=np.asarray(scaled_deltas,dtype=np.float64);a=np.asarray(anchor,dtype=np.float64)
    if y.ndim!=2 or y.shape[1] not in (1,5) or a.shape!=(len(y),) or len(y)==0:
        raise ValueError('Invalid residual output/anchor shapes')
    if not np.isfinite(y).all() or not np.isfinite(a).all() or (a<=0).any():
        raise ValueError('Invalid residual output/anchor values')
    output=a[:,None]+y*_scale(training_scale)
    if not np.isfinite(output).all():raise ValueError('Nonfinite decoded prices')
    return output
