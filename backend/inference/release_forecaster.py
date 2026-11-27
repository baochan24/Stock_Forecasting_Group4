"""Input-only historical research inference for the explicit residual release."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from backend.artifacts.research_release import RELEASE_ID,validate_release
from backend.audit.tv6_protocol import resolve_member
from backend.artifacts.scaler import load_scaler
from backend.artifacts.cnn_checkpoint import PROVENANCE,fingerprint,load_cnn_checkpoint
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.data.preparation.tensors import make_lstm_inputs
from backend.data.preparation.preparation import target_split
from backend.data.transforms.anchored_price import encode_history,decode_prices
from backend.data.transforms.scaling import inverse_scale
from backend.baselines.persistence import predict_persistence


class ReleaseForecaster:
    def __init__(self,root,release_id=RELEASE_ID):
        self._root=Path(root).resolve();self._release_id=release_id
        self._manifest=validate_release(self._root,release_id)
        torch.set_num_threads(self._manifest['semantic']['torch_threads'])

    @property
    def metadata(self):
        s=self._manifest['semantic']
        return deepcopy({k:s[k] for k in ['release_id','kind','dataset_version','lookback','dtype','demo_seed','independent_holdout','limitations']})

    def predict(self,inputs,*,methods=None,seed=42):
        document=validate_release(self._root,self._release_id)
        if document!=self._manifest:raise ValueError('Release changed during engine lifetime')
        s=document['semantic']
        if torch.get_num_threads()!=s['torch_threads']:raise ValueError('Runtime thread contract changed')
        if type(seed) is not int or seed not in (42,123,456):raise ValueError('Expected locked integer seed')
        if methods is None:methods=['lstm','persistence']
        if (not isinstance(methods,list) or not methods or any(not isinstance(m,str) for m in methods)
                or len(set(methods))!=len(methods) or set(methods)-{'lstm','cnn','persistence'}):raise ValueError('Invalid method list')
        if not isinstance(inputs,list) or not inputs or not isinstance(inputs[0],dict):raise ValueError('Nonempty input records required')
        h=inputs[0].get('forecast_length')
        if type(h) is not int or h not in (1,5) or (h==5 and 'cnn' in methods):raise ValueError('Unsupported method/horizon')
        catalog={(m['method'],m['forecast_length'],m['seed']):m for m in s['models']}
        entry=catalog[('lstm',h,seed)]
        scaler,_=load_scaler(self._root/'artifacts/scalers'/entry['scaler_id'],expected_dataset_version=s['dataset_version'],expected_source_hashes=s['source_hashes'])
        packed=make_lstm_inputs(inputs,scaler,dataset_version=s['dataset_version'],forecast_length=h)
        records=packed['inputs'];raw=np.stack([r['input_values'] for r in records]).astype(np.float64)
        if raw.shape[1:]!=(30,1):raise ValueError('Release requires lookback30')
        frame=pd.read_csv(resolve_member(self._root,s['snapshot']),float_precision='round_trip')
        dates=frame.date.tolist();prices=frame.adjusted_close.to_numpy(dtype=np.float64);positions={d:i for i,d in enumerate(dates)}
        future=[];splits=[]
        for record,values in zip(records,raw):
            i=positions.get(record['forecast_origin'])
            if i is None or i<29 or record['input_dates']!=dates[i-29:i+1]:raise ValueError('Input sessions differ from release snapshot')
            if not np.allclose(values[:,0],prices[i-29:i+1],rtol=0,atol=1e-12):raise ValueError('Input prices differ from release snapshot')
            days=dates[i+1:i+1+h]
            if len(days)!=h:raise ValueError('Future sessions unavailable in historical snapshot')
            split=target_split(days)
            if split not in ('val','test'):raise ValueError('Release allows validation/test target dates within one split only')
            future.append(days);splits.append(split)
        output={}
        for method in methods:
            if method=='persistence':output[method]=(predict_persistence(raw,h),None);continue
            e=catalog[(method,h,seed)];folder=resolve_member(self._root,e['checkpoint'])
            sc,_=load_scaler(self._root/'artifacts/scalers'/e['scaler_id'],expected_dataset_version=s['dataset_version'],expected_source_hashes=s['source_hashes'])
            if method=='lstm':
                model=LSTMOneStep() if h==1 else LSTMMultiStep()
                state=torch.load(folder/'state_dict.pt',map_location='cpu',weights_only=True)
                if not isinstance(state,dict) or any(not isinstance(v,torch.Tensor) or v.dtype!=torch.float64 or not torch.isfinite(v).all() for v in state.values()):
                    raise ValueError('Residual weights must be finite float64 tensors')
                model.load_state_dict(state)
                x,_=encode_history(raw,sc.scale_[0]);x=torch.from_numpy(x)
            else:
                m=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))['metadata']
                model,_=load_cnn_checkpoint(folder,expected_provenance={k:m[k] for k in PROVENANCE},expected_model_config=m['training_config']['model'],
                    expected_training_config_sha256=fingerprint(m['training_config']),expected_run_id=e['run_id'],expected_seed=seed)
                x=make_lstm_inputs(records,sc,dataset_version=s['dataset_version'],forecast_length=h)['X']
            model.eval()
            for p in model.parameters():p.requires_grad_(False)
            with torch.inference_mode():values=torch.cat([model(x[i:i+32]) for i in range(0,len(x),32)]).numpy()
            if values.shape!=(len(records),h) or not np.isfinite(values).all():raise ValueError('Invalid model outputs')
            usd=decode_prices(values,raw[:,-1,0],sc.scale_[0]) if method=='lstm' else inverse_scale(values,sc)
            output[method]=(usd,e)
        rows=[]
        for i,record in enumerate(records):
            for method in methods:
                values,e=output[method]
                for k,day in enumerate(future[i]):
                    rows.append(dict(release_id=s['release_id'],release_sha256=document['semantic_sha256'],dataset_version=s['dataset_version'],
                        sample_id=record['sample_id'],method=method,seed=seed if e else None,run_id=e['run_id'] if e else None,
                        model_version=Path(e['checkpoint']).name if e else None,baseline_version=None if e else 'last-observed-price-v1',
                        scaler_id=e['scaler_id'] if e else None,representation=e['representation'] if e else 'raw-last-observed-price',
                        forecast_origin=record['forecast_origin'],forecast_length=h,horizon_step=k+1,target_date=day,
                        predicted_price=float(values[i,k]),currency='USD',feature='adjusted_close',result_source='inference',
                        scope='historical_validation' if splits[i]=='val' else 'historical_test',independent_holdout=False))
        return deepcopy(rows)
