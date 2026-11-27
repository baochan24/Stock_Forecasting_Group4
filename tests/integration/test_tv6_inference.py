"""Real accepted artifacts, validation only; no test prediction or metric."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from backend.inference.frozen_forecaster import FrozenForecaster

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def engine():return FrozenForecaster(ROOT)


@pytest.fixture(scope='module')
def inputs():
    result={}
    protocol=json.loads((ROOT/'experiments/configs/tv6_evaluation_protocol_v1.json').read_text())
    for cohort in protocol['semantic']['cohorts']:
        h=cohort['forecast_length']
        result[h]=json.loads((ROOT/'data/prepared'/cohort['prepared_id']/f'f{h}_val_inputs.json').read_text())
    return result


@pytest.mark.parametrize('h,methods',[(1,['lstm','cnn','persistence']),(5,['lstm','persistence'])])
def test_shapes_dates_usd_and_baseline(engine,inputs,h,methods):
    records=deepcopy(inputs[h][:2]);before=deepcopy(records)
    rows=engine.predict(records,methods=methods)
    assert len(rows)==2*len(methods)*h and records==before
    assert all(np.isfinite(r['predicted_price']) and r['currency']=='USD' for r in rows)
    assert all('actual' not in r and 'target_values' not in r and 'error_usd' not in r for r in rows)
    for record in records:
        group=[r for r in rows if r['sample_id']==record['sample_id']]
        for method in methods:
            part=[r for r in group if r['method']==method]
            assert [r['horizon_step'] for r in part]==list(range(1,h+1))
            assert all(r['target_date']>record['forecast_origin'] for r in part)
            if method=='persistence':
                assert all(r['predicted_price']==record['input_values'][-1][0] and r['run_id'] is None and r['seed'] is None for r in part)


def test_batch_tail_and_repeat_do_not_change_model(engine,inputs):
    records=inputs[1][:33]
    first=engine.predict(records,methods=['lstm','cnn'])
    before={key:{n:p.clone() for n,p in m.state_dict().items()} for key,m in engine._cache.items()}
    again=engine.predict(records,methods=['lstm','cnn'])
    assert first==again and len(first)==66
    for key,model in engine._cache.items():
        assert not model.training and all(not p.requires_grad and p.grad is None for p in model.parameters())
        assert all(torch.equal(before[key][n],p) for n,p in model.state_dict().items())


@pytest.mark.parametrize('seed',[42,123,456])
def test_research_seeds_pinned(engine,inputs,seed):
    rows=engine.predict(inputs[1][:1],methods=['lstm','cnn'],seed=seed)
    assert all(r['seed']==seed and f'seed{seed}' in r['run_id'] for r in rows)


@pytest.mark.parametrize('damage',['target','raw_price','date_gap','wrong_version','duplicate','mixed_mode','nan','lookback'])
def test_bad_input_rejected(engine,inputs,damage):
    records=deepcopy(inputs[1][:1])
    if damage=='target':records[0]['target_values']=[123.]
    if damage=='raw_price':records[0]['input_values'][0][0]+=10
    if damage=='date_gap':records[0]['input_dates'][0]='2022-01-03'
    if damage=='wrong_version':records[0]['dataset_version']='wrong'
    if damage=='duplicate':records=records*2
    if damage=='mixed_mode':records.append(deepcopy(inputs[5][0]))
    if damage=='nan':records[0]['input_values'][0][0]=float('nan')
    if damage=='lookback':records[0]['lookback']=10
    with pytest.raises(ValueError):engine.predict(records,methods=['lstm'])


@pytest.mark.parametrize('methods,seed',[(['cnn','cnn'],42),(['wrong'],42),([],42),(['lstm'],True),(['lstm'],999)])
def test_bad_method_seed_rejected(engine,inputs,methods,seed):
    with pytest.raises(ValueError):engine.predict(inputs[1][:1],methods=methods,seed=seed)


def test_cnn_multistep_rejected(engine,inputs):
    with pytest.raises(ValueError,match='one-step'):engine.predict(inputs[5][:1],methods=['cnn'])


def test_test_origin_blocked_without_predicting_test(engine,inputs,monkeypatch):
    # Build only the observed history ending 2023-12-29; do not read test targets.
    record=deepcopy(inputs[1][-1]);origin='2023-12-29';i=engine._positions[origin]
    record.update(forecast_origin=origin,input_dates=engine._dates[i-29:i+1],
        input_values=engine._prices[i-29:i+1,None].tolist(),
        sample_id=f"{engine._version}:lb30:f1:{origin}")
    monkeypatch.setattr(engine,'_load_model',lambda *args:pytest.fail('Must reject before loading/forward'))
    with pytest.raises(ValueError,match='validation scope'):engine.predict([record],methods=['lstm'])


def test_no_scaler_fitting(engine,inputs,monkeypatch):
    from sklearn.preprocessing import StandardScaler
    for name in ('fit','partial_fit','fit_transform'):
        monkeypatch.setattr(StandardScaler,name,lambda *a,**k:pytest.fail('Inference must not fit scaler'))
    assert engine.predict(inputs[1][:1],methods=['lstm','persistence'])


def test_guard_failure_prevents_forward(engine,inputs,monkeypatch):
    import backend.inference.frozen_forecaster as module
    def reject(*args,**kwargs):raise ValueError('artifact changed')
    monkeypatch.setattr(module,'validate_protocol',reject)
    monkeypatch.setattr(engine,'_load_model',lambda *a:pytest.fail('Guard must fail before model execution'))
    with pytest.raises(ValueError,match='artifact changed'):engine.predict(inputs[1][:1],methods=['lstm'])


def test_runtime_drift_rejected(engine,inputs):
    before=torch.get_num_threads()
    try:
        torch.set_num_threads(2)
        with pytest.raises(ValueError,match='Runtime threads'):engine.predict(inputs[1][:1],methods=['lstm'])
    finally:torch.set_num_threads(before)
