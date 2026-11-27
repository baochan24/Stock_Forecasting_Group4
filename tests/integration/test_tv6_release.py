from copy import deepcopy
import json,os,uuid
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch
from sklearn.preprocessing import StandardScaler
import backend.artifacts.research_release as release
from backend.audit.tv6_protocol import digest
from backend.inference.release_forecaster import ReleaseForecaster

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture
def engine(monkeypatch):
    monkeypatch.setattr(release,'REGISTRY',os.environ.get('TV6_RELEASE_TEST_REGISTRY',release.REGISTRY))
    return ReleaseForecaster(ROOT)


def records(engine,h=1,origins=('2023-06-15','2025-06-16')):
    s=engine._manifest['semantic'];frame=pd.read_csv(ROOT/s['snapshot'],float_precision='round_trip')
    days=frame.date.tolist();prices=frame.adjusted_close.tolist();rows=[]
    for origin in origins:
        i=days.index(origin)
        rows.append(dict(sample_id=f'{s["dataset_version"]}:lb30:f{h}:{origin}',dataset_version=s['dataset_version'],forecast_origin=origin,
            input_dates=days[i-29:i+1],input_values=[[v] for v in prices[i-29:i+1]],lookback=30,forecast_length=h))
    return rows


@pytest.mark.parametrize('h',[1,5])
def test_shapes_identity_dates_baseline_and_repeat_no_fit(engine,h,monkeypatch):
    monkeypatch.setattr(StandardScaler,'fit',lambda *a,**k:pytest.fail('fit forbidden'))
    monkeypatch.setattr(StandardScaler,'partial_fit',lambda *a,**k:pytest.fail('partial_fit forbidden'))
    inputs=records(engine,h);before=deepcopy(inputs)
    methods=['lstm','cnn','persistence'] if h==1 else ['lstm','persistence']
    rows=engine.predict(inputs,methods=methods)
    assert rows==engine.predict(inputs,methods=methods) and inputs==before
    assert len(rows)==2*h*len(methods)
    for r in rows:
        assert r['release_id']==release.RELEASE_ID and r['currency']=='USD'
        assert not {'actual_price','target_values','error_usd'}&set(r)
        assert np.isfinite(r['predicted_price']) and r['independent_holdout'] is False
        if r['method']=='persistence':
            source=next(x for x in inputs if x['sample_id']==r['sample_id'])
            assert r['predicted_price']==source['input_values'][-1][0] and r['seed'] is None


@pytest.mark.parametrize('seed',[43,True,'42'])
def test_reject_seed_before_forward(engine,seed,monkeypatch):
    monkeypatch.setattr(torch,'load',lambda *a,**k:pytest.fail('forward/load must not start'))
    with pytest.raises(ValueError):engine.predict(records(engine),seed=seed)


@pytest.mark.parametrize('bad',['target','price','date','version','lookback','duplicate'])
def test_reject_bad_input_before_load(engine,bad,monkeypatch):
    x=records(engine,origins=('2023-06-15',))
    if bad=='target':x[0]['target_values']=[999.]
    if bad=='price':x[0]['input_values'][0][0]+=1
    if bad=='date':x[0]['input_dates'][0]='2000-01-03'
    if bad=='version':x[0]['dataset_version']='wrong'
    if bad=='lookback':x[0]['lookback']=29
    if bad=='duplicate':x.append(deepcopy(x[0]))
    monkeypatch.setattr(torch,'load',lambda *a,**k:pytest.fail('invalid input reached weight load'))
    with pytest.raises(ValueError):engine.predict(x)


def test_cross_split_and_cnn_h5_rejected(engine,monkeypatch):
    monkeypatch.setattr(torch,'load',lambda *a,**k:pytest.fail('invalid mode reached weight load'))
    with pytest.raises(ValueError):engine.predict(records(engine,5,('2023-12-27',)))
    with pytest.raises(ValueError):engine.predict(records(engine,5),methods=['cnn'])


def test_file_tamper_detected_before_weight_load(engine,monkeypatch):
    original=release.file_hash
    monkeypatch.setattr(release,'file_hash',lambda p:'0'*64 if p.name=='state_dict.pt' else original(p))
    monkeypatch.setattr(torch,'load',lambda *a,**k:pytest.fail('corrupt artifact reached loader'))
    with pytest.raises(ValueError,match='checksum'):engine.predict(records(engine))


def test_wrong_scaler_even_in_resigned_manifest_rejected(engine,monkeypatch):
    folder=ROOT/'logs/audit'/('tv6_release_negative_'+uuid.uuid4().hex);folder.mkdir()
    document=deepcopy(engine._manifest);s=document['semantic']
    s['models'][0]['scaler_id']=next(m['scaler_id'] for m in s['models'] if m['method']=='cnn')
    document['semantic_sha256']=digest(s)
    manifest=folder/'manifest.json';manifest.write_text(json.dumps(document))
    registry=dict(release_id=release.RELEASE_ID,manifest=manifest.relative_to(ROOT).as_posix(),
        manifest_sha256=release.file_hash(manifest),semantic_sha256=document['semantic_sha256'])
    rp=folder/'registry.json';rp.write_text(json.dumps(registry))
    monkeypatch.setattr(release,'REGISTRY',rp.relative_to(ROOT).as_posix())
    with pytest.raises(ValueError,match='linkage'):ReleaseForecaster(ROOT)
