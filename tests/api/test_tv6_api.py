import json,math
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.preprocessing import StandardScaler
from backend.api.app import create_app
from backend.inference.release_forecaster import ReleaseForecaster
from backend.artifacts.research_release import RELEASE_ID

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def app():
    app=create_app(ROOT)
    app.state.service.ready()
    return app


@pytest.fixture(scope='module')
def client(app):
    with TestClient(app,raise_server_exceptions=False) as client:yield client


@pytest.mark.parametrize('h',[1,5])
@pytest.mark.parametrize('seed',[42,123,456])
@pytest.mark.parametrize('origin',['2023-06-15','2025-06-16'])
def test_predictions_match_release_and_target_separation(client,h,seed,origin,monkeypatch):
    monkeypatch.setattr(StandardScaler,'fit',lambda *a,**k:pytest.fail('API fit forbidden'))
    monkeypatch.setattr(StandardScaler,'partial_fit',lambda *a,**k:pytest.fail('API partial_fit forbidden'))
    methods=['lstm','cnn','persistence'] if h==1 else ['lstm','persistence']
    response=client.post('/api/v1/predictions',json=dict(release_id=RELEASE_ID,forecast_origin=origin,forecast_length=h,methods=methods,seed=seed))
    assert response.status_code==200,response.text
    body=response.json();assert body['request_id']==response.headers['X-Request-ID']
    assert body['status']=='complete' and body['result_source']=='inference'
    expected=ReleaseForecaster(ROOT).predict([body['input']],methods=methods,seed=seed)
    assert body['predictions']==expected and len(expected)==h*len(methods)
    assert not any('actual_price' in p or 'error_usd' in p for p in expected)
    assert len(body['comparison'])==len(expected)
    for p,c in zip(expected,body['comparison']):assert c['error_usd']==pytest.approx(p['predicted_price']-c['actual_price'])


@pytest.mark.parametrize('patch,status',[
    ({'forecast_origin':'2023-06-17'},422),({'forecast_origin':'2026-01-02'},422),
    ({'forecast_origin':'2022-06-15'},422),({'forecast_origin':'2025-12-31'},422),
    ({'forecast_origin':'2023-02-30'},422),({'forecast_length':2},422),({'forecast_length':True},422),
    ({'seed':43},422),({'seed':True},422),({'target_values':[1.]},422),({'checkpoint_path':'private.pt'},422),
    ({'methods':['lstm','lstm']},422),({'methods':['unknown']},422),
    ({'forecast_length':5,'methods':['cnn']},422),({'forecast_length':5,'forecast_origin':'2023-12-27'},422),
    ({'release_id':'unknown'},404)])
def test_invalid_requests_do_not_reach_inference(client,patch,status,monkeypatch):
    monkeypatch.setattr(ReleaseForecaster,'predict',lambda *a,**k:pytest.fail('invalid request reached inference'))
    body=dict(forecast_origin='2023-06-15');body.update(patch)
    response=client.post('/api/v1/predictions',json=body)
    assert response.status_code==status,response.text
    error=response.json();assert error['status']=='failed' and error['request_id']==response.headers['X-Request-ID']
    assert 'Traceback' not in response.text and 'D:\\' not in response.text


def test_health_and_readiness_have_different_dependencies(client,app,monkeypatch):
    monkeypatch.setattr(app.state.service.results,'validate',lambda *a:(_ for _ in ()).throw(ValueError('D:\\private\\sidecar.csv')))
    assert client.get('/api/v1/health').status_code==200
    response=client.get('/api/v1/readiness')
    assert response.status_code==503 and 'private' not in response.text


def test_unknown_release_dataset_run_and_path(client):
    assert client.get('/api/v1/releases/unknown').status_code==404
    assert client.get('/api/v1/datasets/unknown/prices').status_code==404
    assert client.get('/api/v1/experiments/unknown').status_code==404
    assert client.get('/api/v1/experiments/unknown/audits').status_code==404
    assert client.get('/api/v1/experiments/..%2F..%2Fsecrets').status_code==404


def test_unexpected_errors_are_sanitized(client,app,monkeypatch):
    def fail(*a,**k):raise RuntimeError('D:\\private\\model.pt')
    monkeypatch.setattr(app.state.service,'predict',fail)
    response=client.post('/api/v1/predictions',json={'forecast_origin':'2023-06-15'})
    assert response.status_code==500 and response.json()['error']['code']=='internal_error'
    assert 'private' not in response.text


def test_incomplete_model_output_is_not_reported_complete(client,monkeypatch):
    monkeypatch.setattr(ReleaseForecaster,'predict',lambda *a,**k:[])
    response=client.post('/api/v1/predictions',json={'forecast_origin':'2023-06-15'})
    assert response.status_code==503 and response.json()['error']['code']=='incomplete_inference'


def test_cors_header_survives_sanitized_internal_error(client,app,monkeypatch):
    def fail(*a,**k):raise RuntimeError('internal detail')
    monkeypatch.setattr(app.state.service,'predict',fail)
    response=client.post('/api/v1/predictions',json={'forecast_origin':'2023-06-15'},headers={'Origin':'http://localhost:5173'})
    assert response.status_code==500 and response.headers['access-control-allow-origin']=='http://localhost:5173'


def test_release_metadata_origins_prices_and_pagination(client):
    current=client.get('/api/v1/releases/current');assert current.status_code==200
    data=current.json();assert len(data['experiments'])==9 and data['independent_holdout'] is False
    assert client.get('/api/v1/releases/'+RELEASE_ID).json()['release_sha256']==data['release_sha256']
    for h,total in [(1,752),(5,744)]:
        p=client.get('/api/v1/forecast-origins',params={'forecast_length':h,'limit':2,'offset':1}).json()
        assert p['total']==total and len(p['items'])==2
    p=client.get('/api/v1/forecast-origins',params={'forecast_length':5,'origin_from':'2023-12-27','origin_to':'2023-12-27'}).json()
    assert p['total']==0
    p=client.get('/api/v1/datasets/'+data['dataset_version']+'/prices',params={'start_date':'2023-06-15','end_date':'2023-06-16','limit':1}).json()
    assert p['total']==2 and len(p['items'])==1 and p['items'][0]['date']=='2023-06-15'


@pytest.mark.parametrize('params',[{'limit':1001},{'forecast_length':2},{'seed':43},{'target_values':'1'},
    {'forecast_length':5,'methods':'cnn'},{'origin_from':'2025-01-02','origin_to':'2024-01-02'}])
def test_query_constraints(client,params):assert client.get('/api/v1/results',params=params).status_code==422


@pytest.mark.parametrize('h',[1,5])
def test_stored_results_and_selected_metrics_same_cohort(client,h):
    params=dict(forecast_length=h,origin_from='2025-06-01',origin_to='2025-06-16',limit=1000)
    result=client.get('/api/v1/results',params=params);assert result.status_code==200,result.text
    rows=result.json()['items'];assert rows and all(r['result_source']=='stored_results' for r in rows)
    response=client.get('/api/v1/metrics',params=params);assert response.status_code==200,response.text
    for metric in response.json()['items']:
        p=[r for r in rows if r['method']==metric['method'] and (metric['horizon_step'] is None or r['horizon_step']==metric['horizon_step'])]
        error=[r['predicted_price']-r['actual_price'] for r in p]
        assert metric['range_kind']=='selected_range' and metric['error_count']==len(error)
        assert metric['mae_usd']==pytest.approx(math.fsum(abs(v) for v in error)/len(error),abs=1e-12)
        assert metric['rmse_usd']==pytest.approx(math.sqrt(math.fsum(v*v for v in error)/len(error)),abs=1e-12)
        assert metric['sample_count']==len({r['sample_id'] for r in p})
    full=client.get('/api/v1/metrics',params={'forecast_length':h}).json()
    assert all(m['sample_count']==(502 if h==1 else 498) for m in full['items'])
    if h==5:assert all(m['error_count']==2490 for m in full['items'] if m['metric_scope']=='overall')
    page=client.get('/api/v1/metrics',params={'forecast_length':h,'limit':1}).json()
    assert len(page['items'])==1 and page['total']==(2 if h==1 else 12)


def test_experiment_history_and_audit_bound_to_release(client):
    run=client.get('/api/v1/releases/current').json()['experiments'][0]['run_id']
    result=client.get('/api/v1/experiments/'+run,params={'limit':2});assert result.status_code==200,result.text
    data=result.json();assert data['run_id']==run and len(data['history']['items'])==2
    assert 'output' not in data['configuration'] and 'checkpoint_dir' not in result.text
    audit=client.get('/api/v1/experiments/'+run+'/audits').json()
    assert audit['release_id']==RELEASE_ID and audit['status']=='accepted_local'


@pytest.mark.parametrize('h,detail',[(1,'summary'),(5,'full')])
def test_verified_traces_use_same_checkpoint_and_decode(client,h,detail):
    body=dict(forecast_origin='2023-06-15',forecast_length=h,detail=detail)
    response=client.post('/api/v1/model-traces',json=body);assert response.status_code==200,response.text
    trace=response.json()['trace'];assert trace['verification']['passed'] and len(trace['steps'])==30
    predicted=client.post('/api/v1/predictions',json={k:v for k,v in body.items() if k!='detail'}).json()['predictions']
    expected=[r['predicted_price'] for r in predicted if r['method']=='lstm']
    np.testing.assert_allclose(trace['predicted_prices_usd'],expected,rtol=0,atol=1e-10)
    if detail=='summary':assert isinstance(trace['steps'][0]['forget_gate'],float)
    else:assert len(trace['steps'][0]['forget_gate'])==32


def test_cors_openapi_and_no_training_endpoint(client):
    response=client.options('/api/v1/predictions',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST'})
    assert response.headers.get('access-control-allow-origin')=='http://localhost:5173'
    schema=client.get('/openapi.json').json()
    assert '/api/v1/predictions' in schema['paths'] and '/api/v1/readiness' in schema['paths']
    assert not any('train' in p for p in schema['paths'])
    assert client.post('/api/v1/train',json={}).status_code==404


@pytest.mark.parametrize('schema_name,route',[('PredictionRequest','predictions'),('TraceRequest','model-traces')])
def test_swagger_examples_are_executable(client,schema_name,route):
    schema=client.get('/openapi.json').json()['components']['schemas'][schema_name]
    for example in schema['examples']:
        response=client.post('/api/v1/'+route,json=example)
        assert response.status_code==200,response.text


@pytest.mark.parametrize('defect',['duplicate','actual_mismatch','missing_sample'])
def test_metrics_reject_inconsistent_cohorts(app,defect):
    import pandas as pd
    service=app.state.service
    release=service.ready()
    frame=service.results.select(release,1,42,['lstm','persistence'],'val','2023-06-15','2023-06-16')
    if defect=='duplicate':frame=pd.concat([frame,frame.iloc[[0]]],ignore_index=True)
    elif defect=='actual_mismatch':frame.loc[frame.method=='persistence','actual_price']+=1
    else:frame=frame.drop(frame[frame.method=='persistence'].index[0])
    with pytest.raises(ValueError):service.results.metrics(frame,['lstm','persistence'],'selected_range')
