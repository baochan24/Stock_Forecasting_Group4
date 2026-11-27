"""Version-bound stored results, experiment histories and shared USD metrics."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from backend.audit.tv6_protocol import digest,resolve_member
from backend.artifacts.research_release import file_hash
from backend.evaluation.one_step import evaluate_one_step

REGISTRY='experiments/configs/tv6_api_data_v1.registry.json'


def records(frame):
    return frame.astype(object).where(pd.notna(frame),None).to_dict('records')


class ReleaseResults:
    def __init__(self,root):self.root=Path(root).resolve();self._cache=None;self._fingerprint=None

    def validate(self,release):
        document=json.loads((self.root/REGISTRY).read_text(encoding='utf-8'));s=document['semantic']
        if digest(s)!=document['semantic_sha256'] or s['release_id']!=release['semantic']['release_id'] or s['release_sha256']!=release['semantic_sha256']:
            raise ValueError('Stored results do not match release')
        for name,sha in s['files_sha256'].items():
            if file_hash(resolve_member(self.root,name))!=sha:raise ValueError('Stored results integrity failure')
        if self._cache is None or self._fingerprint!=document['semantic_sha256']:
            frame=pd.read_csv(resolve_member(self.root,s['results']),float_precision='round_trip')
            if len(frame)!=s['rows'] or not (frame.release_sha256==release['semantic_sha256']).all():raise ValueError('Mixed/incomplete stored release')
            self._cache=frame;self._fingerprint=document['semantic_sha256']
        return s

    def select(self,release,h,seed,methods,split,origin_from=None,origin_to=None):
        self.validate(release);f=self._cache
        scope='historical_validation' if split=='val' else 'historical_test'
        f=f[(f.forecast_length==h)&(f.scope==scope)&f.method.isin(methods)&((f.seed==seed)|f.seed.isna())]
        if origin_from:f=f[f.forecast_origin>=origin_from]
        if origin_to:f=f[f.forecast_origin<=origin_to]
        return f.sort_values(['forecast_origin','method','horizon_step']).copy()

    def metrics(self,frame,methods,range_kind):
        if frame.empty:raise ValueError('Selected range has no stored samples')
        output=[];reference=None;reference_actual=None
        for method in methods:
            g=frame[frame.method==method].sort_values(['forecast_origin','horizon_step'])
            keys=list(zip(g.sample_id,g.forecast_origin,g.target_date,g.horizon_step))
            if len(set(keys))!=len(keys):raise ValueError('Duplicate stored sample keys')
            if not keys or (reference is not None and keys!=reference):raise ValueError('Methods do not cover the same selected samples')
            actual=g.actual_price.to_numpy()
            if reference_actual is not None and not np.array_equal(actual,reference_actual):raise ValueError('Methods disagree on actual prices')
            reference_actual=actual
            reference=keys;h=int(g.forecast_length.iloc[0])
            for step in list(range(1,h+1))+([0] if h==5 else []):
                p=g if step==0 else g[g.horizon_step==step]
                k=list(zip(p.sample_id,p.target_date,p.horizon_step))
                result=evaluate_one_step(p.actual_price.to_numpy().reshape(-1,1),p.predicted_price.to_numpy().reshape(-1,1),target_keys=k,prediction_keys=k)
                output.append(dict(method=method,seed=None if method=='persistence' else int(g.seed.iloc[0]),forecast_length=h,
                    horizon_step=None if step==0 else step,metric_scope='overall' if step==0 else 'per_horizon',
                    sample_count=p.sample_id.nunique(),error_count=len(p),mae_usd=result['mae_usd'],rmse_usd=result['rmse_usd'],
                    currency='USD',range_kind=range_kind,evaluation_phase=g.evaluation_phase.iloc[0],independent_holdout=False))
        return output

    def experiment(self,release,run_id,offset,limit):
        s=self.validate(release);e=next((e for e in s['experiments'] if e['run_id']==run_id),None)
        if e is None:raise KeyError('Unknown experiment')
        metadata=json.loads(resolve_member(self.root,e['metadata']).read_text(encoding='utf-8'))
        config=metadata['configuration']
        metadata['configuration']={k:config[k] for k in ('model','training','runtime','seeds') if k in config}
        history=pd.read_csv(resolve_member(self.root,e['history']),float_precision='round_trip')
        return dict(**metadata,history=dict(total=len(history),offset=offset,limit=limit,items=records(history.iloc[offset:offset+limit])))
