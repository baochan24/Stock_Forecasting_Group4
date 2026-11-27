"""Strict USD evaluation of full aligned forecast records, separate from inference."""
from pathlib import Path
import numbers
import hashlib
import json
from datetime import date
import numpy as np
import pandas as pd

from backend.audit.tv6_protocol import digest,resolve_member
from backend.evaluation.one_step import evaluate_one_step

KEYS=['sample_id','forecast_origin','forecast_length','horizon_step','target_date','dataset_version']


def _numeric(series,name):
    values=series.to_numpy()
    if values.dtype.kind not in 'iuf' or not np.isfinite(values).all():
        raise ValueError('Expected finite real numbers: '+name)
    return values.astype(np.float64)


def _integer(series,name):
    values=_numeric(series,name)
    if not np.equal(values,np.floor(values)).all():raise ValueError('Expected integer '+name)
    return values.astype(np.int64)


def _keys(frame):return list(frame[KEYS].itertuples(index=False,name=None))


def _seed(value,method):
    if method=='persistence':
        if not pd.isna(value):raise ValueError('Persistence must not have a seed')
        return -1
    if (isinstance(value,(bool,np.bool_)) or not isinstance(value,numbers.Real)
            or not np.isfinite(value) or value not in (42,123,456)):
        raise ValueError('Expected all locked neural seeds')
    return int(value)


def load_validation_cohorts(root,protocol):
    """Derive full validation keys from hash-pinned source, not submitted rows."""
    cohorts=[]
    for cohort in protocol['semantic']['cohorts']:
        h=cohort['forecast_length'];base=f"data/prepared/{cohort['prepared_id']}/"
        payloads=[]
        for suffix in ('inputs','targets'):
            name=base+f'f{h}_val_{suffix}.json'
            expected=protocol['semantic']['artifacts_sha256'].get(name)
            if expected is None:raise ValueError('Validation source is not pinned')
            raw=resolve_member(root,name).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Validation source checksum mismatch')
            payloads.append(json.loads(raw.decode('utf-8')))
        inputs,targets=payloads
        if not inputs or len(inputs)!=len(targets):raise ValueError('Incomplete validation source')
        keys=[]
        for x,y in zip(inputs,targets):
            if x['sample_id']!=y['sample_id'] or y['split']!='val' or len(y['target_dates'])!=h:
                raise ValueError('Validation source pairing/split mismatch')
            keys.append(dict(sample_id=x['sample_id'],forecast_origin=x['forecast_origin'],target_dates=y['target_dates']))
        cohorts.append(dict(forecast_length=h,samples=len(keys),ordered_keys_sha256=digest(keys)))
    return cohorts


def evaluate_forecast_records(predictions,actuals,*,protocol,split='val',forecast_lengths=(1,5),expected_validation_cohorts=None):
    """Return per-run metrics, seed aggregates and correctly joined residuals.

    Caller validates the frozen protocol/artifacts and supplies source actuals.
    Full-test inputs additionally must match locked cohort keys/counts. No
    partial ranges or silent intersections are accepted by this entry point.
    """
    if (split not in ('val','test') or not forecast_lengths or set(forecast_lengths)-{1,5}
            or any(type(h) is not int for h in forecast_lengths)):
        raise ValueError('Unsupported split/modes')
    if len(set(forecast_lengths))!=len(forecast_lengths):raise ValueError('Duplicate modes')
    if split=='val' and expected_validation_cohorts is None:
        raise ValueError('Full validation requires independently accepted cohort keys')
    semantic=protocol['semantic']
    if digest(semantic)!=protocol['semantic_sha256']:raise ValueError('Protocol fingerprint mismatch')
    pred=predictions.copy(deep=True);actual=actuals.copy(deep=True)
    required=set(KEYS)|{'method','seed','run_id','model_version','baseline_version','predicted_price',
        'protocol_id','protocol_sha256','scaler_id','currency','feature','result_source','scope','release_id'}
    if pred.empty or actual.empty or not required.issubset(pred) or not (set(KEYS)|{'actual_price','split'}).issubset(actual):
        raise ValueError('Missing forecast/actual columns or empty input')
    if {'actual_price','actual_usd','error_usd','target_values'}&set(pred):raise ValueError('Predictions already contain actual/error fields')
    for frame in (pred,actual):
        for key in ('forecast_length','horizon_step'):frame[key]=_integer(frame[key],key)
        if set(frame.forecast_length)!=set(forecast_lengths):raise ValueError('Missing/extra forecast modes')
        if frame[KEYS].isna().any().any():raise ValueError('Null alignment key')
        for key in ('forecast_origin','target_date'):
            for value in frame[key].tolist():
                if not isinstance(value,str) or len(value)!=10 or date.fromisoformat(value).isoformat()!=value:
                    raise ValueError('Expected canonical ISO session dates')
        if not (frame.dataset_version==semantic['dataset_version']).all():raise ValueError('Mixed dataset versions')
    actual['actual_price']=_numeric(actual.actual_price,'actual_price')
    pred['predicted_price']=_numeric(pred.predicted_price,'predicted_price')
    if not (actual.actual_price>0).all() or not (actual.split==split).all():raise ValueError('Wrong raw actual price/split')
    if actual.duplicated(KEYS).any():raise ValueError('Duplicate actual key')
    scope='validation' if split=='val' else 'test'
    checks={'protocol_id':semantic['protocol_id'],'protocol_sha256':protocol['semantic_sha256'],
        'scaler_id':semantic['models'][0]['scaler_id'],'currency':'USD','feature':'adjusted_close',
        'result_source':'inference','scope':scope}
    for key,wanted in checks.items():
        if not (pred[key]==wanted).all():raise ValueError('Mixed/wrong forecast context: '+key)
    if pred.release_id.nunique(dropna=False)!=1:raise ValueError('Mixed releases')
    if pred.method.isna().any() or not pred.method.isin(['lstm','cnn','persistence']).all():raise ValueError('Unknown method')
    pred['_seed']=[_seed(s,m) for s,m in zip(pred.seed,pred.method)]
    catalog={(m['method'].lower(),m['forecast_length'],m['seed']):m for m in semantic['models'] if m['forecast_length'] in forecast_lengths}
    expected=set(catalog)|{('persistence',h,-1) for h in forecast_lengths}
    groups={(m,int(h),int(s)):g for (m,h,s),g in pred.groupby(['method','forecast_length','_seed'],sort=False)}
    if set(groups)!=expected:raise ValueError('Missing/extra model seeds or baseline modes')
    for h in forecast_lengths:
        part=actual[actual.forecast_length==h]
        sample_order=list(dict.fromkeys(part.sample_id))
        if len(part)!=len(sample_order)*h:raise ValueError('Incomplete sample/horizon coverage')
        cohort=[]
        origins=[]
        for sample in sample_order:
            sample_rows=part[part.sample_id==sample]
            if sample_rows.horizon_step.tolist()!=list(range(1,h+1)) or sample_rows.forecast_origin.nunique()!=1:
                raise ValueError('Missing/reordered horizon or mixed origins')
            origin=sample_rows.forecast_origin.iloc[0];dates=sample_rows.target_date.tolist()
            if dates!=sorted(set(dates)) or not all(d>origin for d in dates):raise ValueError('Wrong target date order')
            expected_id=f"{semantic['dataset_version']}:lb30:f{h}:{origin}"
            if sample!=expected_id:raise ValueError('Sample identity/mode/origin mismatch')
            lower,upper=('2023-01-01','2023-12-31') if split=='val' else ('2024-01-01','2025-12-31')
            if not all(lower<=d<=upper for d in dates):raise ValueError('Target outside requested split')
            origins.append(origin)
            cohort.append(dict(sample_id=sample,forecast_origin=origin,target_dates=dates))
        if origins!=sorted(set(origins)):raise ValueError('Sample origins must be ordered and unique')
        references=semantic['cohorts'] if split=='test' else expected_validation_cohorts
        matching=[c for c in references if c['forecast_length']==h]
        if len(matching)!=1:raise ValueError('Missing/duplicate accepted cohort mode')
        locked=matching[0]
        if len(cohort)!=locked['samples'] or digest(cohort)!=locked['ordered_keys_sha256']:
            raise ValueError('Full '+split+' cohort differs from accepted source/protocol')
    metrics=[];joined=[]
    for (method,h,seed),group in groups.items():
        truth=actual[actual.forecast_length==h]
        if _keys(group)!=_keys(truth):raise ValueError('Missing/extra/duplicate/reordered prediction keys')
        if method=='persistence':
            if group.run_id.notna().any() or group.model_version.notna().any() or not (group.baseline_version=='last-observed-price-v1').all():
                raise ValueError('Wrong baseline identity')
        else:
            model=catalog[(method,h,seed)]
            if not (group.run_id==model['run_id']).all() or not (group.model_version==Path(model['checkpoint']).name).all() or group.baseline_version.notna().any():
                raise ValueError('Wrong model/run/seed identity')
        common=dict(method=method,forecast_length=h,seed=None if seed==-1 else seed,split=split,
            protocol_id=semantic['protocol_id'],protocol_sha256=protocol['semantic_sha256'],currency='USD',
            range_kind='validation_full_set' if split=='val' else 'official_full_set')
        for step in list(range(1,h+1))+([0] if h==5 else []):
            mask=np.ones(len(group),dtype=bool) if step==0 else group.horizon_step.to_numpy()==step
            a=truth.actual_price.to_numpy()[mask].reshape(-1,1)
            p=group.predicted_price.to_numpy()[mask].reshape(-1,1)
            keys=[k for k,use in zip(_keys(truth),mask) if use]
            with np.errstate(over='ignore',invalid='ignore'):
                metric=evaluate_one_step(a,p,target_keys=keys,prediction_keys=keys)
            if not np.isfinite([metric['mae_usd'],metric['rmse_usd']]).all():
                raise ValueError('Nonfinite derived metric/overflow')
            metrics.append(dict(**common,horizon_step=None if step==0 else step,metric_scope='overall' if step==0 else 'per_horizon',
                sample_count=truth.sample_id.nunique(),error_count=len(a),mae_usd=metric['mae_usd'],rmse_usd=metric['rmse_usd']))
        residuals=group.drop(columns=['_seed']).copy()
        residuals['actual_price']=truth.actual_price.to_numpy()
        residuals['error_usd']=residuals.predicted_price-residuals.actual_price
        joined.append(residuals)
    metrics=pd.DataFrame(metrics);aggregates=[]
    for (method,h,step),part in metrics[metrics.method!='persistence'].groupby(['method','forecast_length','horizon_step'],sort=False,dropna=False):
        if sorted(part.seed.tolist())!=[42,123,456] or part.sample_count.nunique()!=1 or part.error_count.nunique()!=1:
            raise ValueError('Incomplete or inconsistent seed aggregation')
        overall=pd.isna(step)
        aggregates.append(dict(method=method,forecast_length=int(h),horizon_step=None if overall else int(step),seeds=3,
            split=split,currency='USD',sample_count=int(part.sample_count.iloc[0]),error_count=int(part.error_count.iloc[0]),
            protocol_id=semantic['protocol_id'],protocol_sha256=protocol['semantic_sha256'],
            metric_scope='overall' if overall else 'per_horizon',range_kind='validation_full_set' if split=='val' else 'official_full_set',
            mae_usd_mean=float(part.mae_usd.mean()),mae_usd_std=float(part.mae_usd.std(ddof=1)),
            rmse_usd_mean=float(part.rmse_usd.mean()),rmse_usd_std=float(part.rmse_usd.std(ddof=1)),std_ddof=1))
    return dict(metrics=metrics,aggregates=pd.DataFrame(aggregates),residuals=pd.concat(joined,ignore_index=True))
