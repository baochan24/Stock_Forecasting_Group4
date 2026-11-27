"""Input-only research inference for the accepted TV6 validation scope.

Test execution is deliberately not enabled before the final evaluator exists.
No training, fitting, actual/target joins, metrics or release selection here.
"""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from backend.audit.tv6_protocol import PROTOCOL_PATH,validate_protocol,resolve_member
from backend.artifacts.cnn_checkpoint import PROVENANCE,fingerprint,load_cnn_checkpoint
from backend.artifacts.lstm_checkpoint import load_lstm_checkpoint
from backend.artifacts.scaler import load_scaler
from backend.baselines.persistence import predict_persistence
from backend.data.preparation.tensors import make_lstm_inputs
from backend.data.transforms.scaling import inverse_scale


class FrozenForecaster:
    """Use the frozen model catalog; default demo seed42, research may use all3.

    This item3 implementation accepts only validation2023 target dates. Future
    test execution must be integrated through the item5 evaluation workflow.
    """
    def __init__(self,root,*,test_run=None):
        self._root=Path(root).resolve()
        self._protocol=json.loads((self._root/PROTOCOL_PATH).read_text(encoding='utf-8'))
        self._hash=validate_protocol(self._protocol,self._root)
        self._test_run=test_run
        if test_run is not None:
            from backend.audit.tv6_test_run import validate_test_run
            validate_test_run(self._root,test_run,self._hash)
        semantic=self._protocol['semantic']
        torch.set_num_threads(semantic['runtime']['torch_threads'])
        self._version=semantic['dataset_version']
        self._catalog={(m['method'].lower(),m['forecast_length'],m['seed']):m for m in semantic['models']}
        inventory=json.loads((self._root/'reports/audits/TV6_Input_Inventory.json').read_text(encoding='utf-8'))
        self._source_hashes=inventory['source_hashes']
        self._scaler_id=semantic['models'][0]['scaler_id']
        self._scaler,_=load_scaler(self._root/'artifacts/scalers'/self._scaler_id,
            expected_dataset_version=self._version,expected_source_hashes=self._source_hashes)
        frame=pd.read_csv(self._root/f'data/validated/aapl_validated_{self._version}.csv')
        self._dates=frame.date.tolist()
        self._prices=frame.adjusted_close.to_numpy(dtype=np.float64)
        self._positions={d:i for i,d in enumerate(self._dates)}
        self._cache={}

    def _load_model(self,method,horizon,seed):
        key=(method,horizon,seed)
        if key not in self._catalog:raise ValueError('Method/mode/seed is not in the frozen catalog')
        if key not in self._cache:
            entry=self._catalog[key]
            folder=resolve_member(self._root,entry['checkpoint'])
            meta=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))['metadata']
            if method=='cnn':
                model,_=load_cnn_checkpoint(folder,expected_provenance={k:meta[k] for k in PROVENANCE},
                    expected_model_config=meta['training_config']['model'],
                    expected_training_config_sha256=fingerprint(meta['training_config']),
                    expected_run_id=entry['run_id'],expected_seed=seed)
            else:
                model,_=load_lstm_checkpoint(folder,expected_dataset_version=self._version,
                    expected_source_hashes=self._source_hashes,expected_scaler_id=self._scaler_id,
                    expected_forecast_length=horizon,expected_lookback=30)
            model.eval()
            for p in model.parameters():p.requires_grad_(False)
            self._cache[key]=model
        return self._cache[key]

    def predict(self,inputs,*,methods,seed=42):
        """Receive only TV2 Forecast Input records, return USD prediction records.

        Accept only server catalog methods and seeds, never arbitrary checkpoint
        paths/scalers or target records. Preserve sample/date order and tails.
        """
        if type(seed) is not int or seed not in (42,123,456):raise ValueError('Expected locked integer seed')
        if (not isinstance(methods,list) or not methods or any(not isinstance(m,str) for m in methods)
                or len(set(methods))!=len(methods) or any(m not in ('lstm','cnn','persistence') for m in methods)):
            raise ValueError('Expected unique supported method list')
        validate_protocol(self._protocol,self._root)
        if self._test_run is not None:
            from backend.audit.tv6_test_run import validate_test_run
            validate_test_run(self._root,self._test_run,self._hash)
        if torch.get_num_threads()!=self._protocol['semantic']['runtime']['torch_threads']:
            raise ValueError('Runtime threads differ from frozen protocol')
        # Adapter rejects target/extra fields, mixed versions/modes and duplicates.
        if not isinstance(inputs,list) or not inputs:raise ValueError('Expected nonempty input record list')
        h=inputs[0].get('forecast_length') if isinstance(inputs[0],dict) else None
        packed=make_lstm_inputs(inputs,self._scaler,dataset_version=self._version,forecast_length=h)
        records=packed['inputs'];x=packed['X']
        if x.shape[1:]!=(30,1):raise ValueError('Frozen release requires lookback30/one feature')
        if h==5 and 'cnn' in methods:raise ValueError('CNN supports one-step only')
        dates=[]
        for record in records:
            i=self._positions.get(record['forecast_origin'])
            if i is None or i<29:raise ValueError('Origin is not an eligible observed session')
            expected_dates=self._dates[i-29:i+1]
            if record['input_dates']!=expected_dates:raise ValueError('Input session sequence differs from accepted history')
            raw=np.asarray(record['input_values'],dtype=np.float64)[:,0]
            if not np.allclose(raw,self._prices[i-29:i+1],rtol=1e-12,atol=1e-12):
                raise ValueError('Input prices differ from frozen snapshot')
            future_dates=self._dates[i+1:i+1+h]
            if len(future_dates)!=h:raise ValueError('Target sessions unavailable in the frozen dataset')
            start,end=('2023-01-01','2023-12-31') if self._test_run is None else ('2024-01-01','2025-12-31')
            if not all(start<=d<=end for d in future_dates):
                raise ValueError('Item3 validation scope only; test inference is not enabled')
            dates.append(future_dates)
        by_method={}
        for method in methods:
            if method=='persistence':
                values=predict_persistence(np.stack([r['input_values'] for r in records]),h)
                entry=None
            else:
                model=self._load_model(method,h,seed)
                with torch.inference_mode():
                    outputs=[model(x[i:i+32]) for i in range(0,len(x),32)]
                    scaled=torch.cat(outputs).numpy()
                if scaled.shape!=(len(records),h) or not np.isfinite(scaled).all():
                    raise ValueError('Invalid inference output shape/finite contract')
                values=inverse_scale(scaled,self._scaler)
                entry=self._catalog[(method,h,seed)]
            by_method[method]=(values,entry)
        rows=[]
        for i,record in enumerate(records):
            for method in methods:
                values,entry=by_method[method]
                for k,target_date in enumerate(dates[i]):
                    rows.append(dict(release_id=None,protocol_id=self._protocol['semantic']['protocol_id'],
                        protocol_sha256=self._hash,dataset_version=self._version,sample_id=record['sample_id'],
                        method=method,seed=seed if entry else None,run_id=entry['run_id'] if entry else None,
                        model_version=Path(entry['checkpoint']).name if entry else None,
                        baseline_version=None if entry else 'last-observed-price-v1',scaler_id=self._scaler_id,
                        forecast_origin=record['forecast_origin'],forecast_length=h,horizon_step=k+1,
                        target_date=target_date,predicted_price=float(values[i,k]),currency='USD',
                        feature='adjusted_close',result_source='inference',scope='validation' if self._test_run is None else 'test'))
        return deepcopy(rows)
