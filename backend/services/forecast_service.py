"""Server-side input construction and release services; no training endpoint."""
import json,threading
from pathlib import Path
import pandas as pd
import numpy as np
import torch
from backend.artifacts.research_release import RELEASE_ID,validate_release
from backend.inference.release_forecaster import ReleaseForecaster
from backend.data.preparation.preparation import target_split
from backend.artifacts.scaler import load_scaler
from backend.data.transforms.anchored_price import encode_history,decode_prices
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.model_trace.lstm_trace import trace_lstm
from backend.services.results.release_results import ReleaseResults,records


class ServiceError(Exception):
    def __init__(self,status,code,message):super().__init__(message);self.status=status;self.code=code;self.message=message


class ResearchService:
    def __init__(self,root):
        self.root=Path(root).resolve();self.results=ReleaseResults(root);self.lock=threading.RLock();self._warmed=None

    def release(self,release_id):
        if release_id!=RELEASE_ID:raise ServiceError(404,'release_not_found','Release not found')
        try:return validate_release(self.root,release_id)
        except Exception as exc:raise ServiceError(503,'release_unavailable','Release artifacts are unavailable or incompatible') from exc

    def ready(self,release_id=RELEASE_ID,warm=True):
        with self.lock:
            release=self.release(release_id)
            try:
                sidecar=self.results.validate(release)
                key=(release['semantic_sha256'],self.results._fingerprint)
                if warm and self._warmed!=key:
                    engine=ReleaseForecaster(self.root)
                    for h in (1,5):
                        x=self.input_record(release,'2023-06-15',h)
                        for seed in (42,123,456):engine.predict([x],methods=['lstm','cnn'] if h==1 else ['lstm'],seed=seed)
                    self._warmed=key
                return release
            except ServiceError:raise
            except Exception as exc:raise ServiceError(503,'release_unavailable','Release data or models are unavailable or incompatible') from exc

    def snapshot(self,release):
        return pd.read_csv(self.root/release['semantic']['snapshot'],float_precision='round_trip')

    def input_record(self,release,origin,h):
        s=release['semantic'];f=self.snapshot(release);days=f.date.tolist()
        if origin not in days:raise ServiceError(422,'invalid_origin','Origin is not an observed trading session')
        i=days.index(origin);future=days[i+1:i+1+h]
        if i<29 or len(future)!=h or target_split(future) not in ('val','test'):
            raise ServiceError(422,'invalid_origin','Origin does not have an eligible historical target window')
        return dict(sample_id=f'{s["dataset_version"]}:lb30:f{h}:{origin}',dataset_version=s['dataset_version'],forecast_origin=origin,
            input_dates=days[i-29:i+1],input_values=[[v] for v in f.adjusted_close.iloc[i-29:i+1]],lookback=30,forecast_length=h)

    def origins(self,release,h,origin_from=None,origin_to=None):
        dates=self.snapshot(release).date.tolist();out=[]
        for i in range(29,len(dates)-h):
            origin=dates[i];future=dates[i+1:i+1+h]
            if target_split(future) in ('val','test') and (origin_from is None or origin>=origin_from) and (origin_to is None or origin<=origin_to):
                out.append(dict(forecast_origin=origin,target_dates=future,split=target_split(future)))
        return out

    def predict(self,release_id,origin,h,methods,seed):
        with self.lock:
            release=self.ready(release_id);record=self.input_record(release,origin,h)
            try:rows=ReleaseForecaster(self.root,release_id).predict([record],methods=methods,seed=seed)
            except Exception as exc:raise ServiceError(503,'inference_unavailable','Inference could not complete for this release') from exc
            if (len(rows)!=h*len(methods) or {(r['method'],r['horizon_step']) for r in rows}!={(m,k) for m in methods for k in range(1,h+1)}):
                raise ServiceError(503,'incomplete_inference','Inference did not return all requested methods and horizons')
            raw=self.snapshot(release).set_index('date').adjusted_close
            comparison=[dict(method=r['method'],horizon_step=r['horizon_step'],target_date=r['target_date'],actual_price=float(raw[r['target_date']]),
                error_usd=float(r['predicted_price']-raw[r['target_date']])) for r in rows]
            return dict(release_id=release_id,dataset_version=release['semantic']['dataset_version'],release_sha256=release['semantic_sha256'],
                result_source='inference',status='complete',input=record,methods=[dict(method=m,status='complete') for m in methods],
                predictions=rows,comparison=comparison,independent_holdout=False,evaluation_note='Historical research; residual was developed after observing the old test.')

    def trace(self,release_id,origin,h,seed,detail):
        with self.lock:
            release=self.ready(release_id);s=release['semantic'];record=self.input_record(release,origin,h)
            e=next(e for e in s['models'] if e['method']=='lstm' and e['forecast_length']==h and e['seed']==seed)
            scaler,_=load_scaler(self.root/'artifacts/scalers'/e['scaler_id'],expected_dataset_version=s['dataset_version'],expected_source_hashes=s['source_hashes'])
            model=LSTMOneStep() if h==1 else LSTMMultiStep()
            model.load_state_dict(torch.load(self.root/e['checkpoint']/'state_dict.pt',map_location='cpu',weights_only=True));model.eval()
            x,anchor=encode_history(np.array([record['input_values']],dtype=np.float64),scaler.scale_[0])
            trace=trace_lstm(model,torch.from_numpy(x))
            if detail=='summary':
                trace['steps']=[dict(time_step=p['time_step'],**{k:float(np.mean(p[k])) for k in ['input_gate','forget_gate','candidate_state','output_gate','hidden_state','cell_state']}) for p in trace['steps']]
            trace['predicted_prices_usd']=decode_prices(np.array([trace['prediction_scaled']]),anchor,scaler.scale_[0])[0].tolist()
            return dict(release_id=release_id,release_sha256=release['semantic_sha256'],dataset_version=s['dataset_version'],run_id=e['run_id'],forecast_origin=origin,
                forecast_length=h,seed=seed,detail=detail,representation=e['representation'],input=record,trace=trace,result_source='verified_model_trace')
