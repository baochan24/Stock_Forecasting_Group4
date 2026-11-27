from copy import deepcopy
import numpy as np
import pandas as pd
import pytest

from backend.audit.tv6_protocol import digest
from backend.evaluation.forecast_records import evaluate_forecast_records as _evaluate,load_validation_cohorts


def evaluate_forecast_records(p,a,*,protocol,**kwargs):
    if kwargs.get('split','val')=='val':kwargs['expected_validation_cohorts']=protocol['validation_cohorts']
    return _evaluate(p,a,protocol=protocol,**kwargs)


def fixture():
    semantic=dict(protocol_id='fixture-protocol',dataset_version='fixture',models=[],cohorts=[])
    for method,h in [('LSTM',1),('CNN',1),('LSTM',5)]:
        for seed in [42,123,456]:
            name=f'{method}_h{h}_seed{seed}'
            semantic['models'].append(dict(method=method,forecast_length=h,seed=seed,
                run_id=name,checkpoint='models/'+name,scaler_id='scalerfixture'))
    protocol=dict(semantic=semantic,semantic_sha256=digest(semantic))
    actual=[]
    for h in (1,5):
        for i,origin in enumerate(['2023-01-02','2023-01-03']):
            dates=pd.bdate_range('2023-01-03',periods=6).strftime('%Y-%m-%d').tolist()[i:i+h]
            for step,day in enumerate(dates,1):
                actual.append(dict(sample_id=f'fixture:lb30:f{h}:{origin}',forecast_origin=origin,
                    forecast_length=h,horizon_step=step,target_date=day,dataset_version='fixture',
                    actual_price=100.+step,split='val'))
    actual=pd.DataFrame(actual);pred=[]
    protocol['validation_cohorts']=[]
    for h in (1,5):
        keys=[dict(sample_id=s,forecast_origin=g.forecast_origin.iloc[0],target_dates=g.target_date.tolist())
            for s,g in actual[actual.forecast_length==h].groupby('sample_id',sort=False)]
        protocol['validation_cohorts'].append(dict(forecast_length=h,samples=len(keys),ordered_keys_sha256=digest(keys)))
    groups=[(m['method'].lower(),m['forecast_length'],m['seed'],m['run_id']) for m in semantic['models']]
    groups+=[('persistence',1,None,None),('persistence',5,None,None)]
    for method,h,seed,run in groups:
        offset=0 if seed is None else [42,123,456].index(seed)
        for i,row in enumerate(actual[actual.forecast_length==h].to_dict('records')):
            values={k:v for k,v in row.items() if k not in ('actual_price','split')}
            error=2*((i%h)+1)-1+(i//h)+offset
            pred.append(dict(**values,method=method,seed=seed,run_id=run,model_version=run,
                baseline_version='last-observed-price-v1' if method=='persistence' else None,
                predicted_price=row['actual_price']+error,protocol_id='fixture-protocol',
                protocol_sha256=protocol['semantic_sha256'],scaler_id='scalerfixture',currency='USD',
                feature='adjusted_close',result_source='inference',scope='validation',release_id=None))
    return pd.DataFrame(pred),actual,protocol


def test_hand_calculated_horizons_overall_and_seed_std():
    p,a,protocol=fixture();p_before=p.copy(deep=True);a_before=a.copy(deep=True)
    result=evaluate_forecast_records(p,a,protocol=protocol)
    metrics=result['metrics']
    overall=metrics[(metrics.method=='lstm')&(metrics.forecast_length==5)&(metrics.seed==42)&(metrics.metric_scope=='overall')].iloc[0]
    assert pd.isna(overall.horizon_step)
    assert overall.mae_usd==5.5 and overall.rmse_usd==pytest.approx(np.sqrt(38.5))
    assert overall.sample_count==2 and overall.error_count==10
    horizons=metrics[(metrics.method=='lstm')&(metrics.forecast_length==5)&(metrics.seed==42)&(metrics.horizon_step>0)]
    assert not np.isclose(overall.rmse_usd,horizons.rmse_usd.mean())
    summary=result['aggregates'];row=summary[(summary.method=='lstm')&(summary.forecast_length==1)].iloc[0]
    assert row.mae_usd_mean==2.5 and row.mae_usd_std==1
    assert row.rmse_usd_std==pytest.approx(np.std(np.sqrt([2.5,6.5,12.5]),ddof=1))
    assert len(metrics)==31 and len(summary)==8 and 'persistence' not in summary.method.tolist()
    pd.testing.assert_frame_equal(p,p_before);pd.testing.assert_frame_equal(a,a_before)


@pytest.mark.parametrize('damage',['missing_prediction','duplicate_prediction','reordered_prediction',
    'wrong_date','wrong_origin','missing_seed','wrong_run','wrong_model','wrong_protocol',
    'wrong_currency','wrong_scope','wrong_dataset','nan','infinite','noninteger_horizon',
    'missing_actual_horizon','duplicate_actual','mixed_actual_split','missing_mode','baseline_seed','baseline_run'])
def test_bad_alignment_or_context_rejected(damage):
    p,a,protocol=fixture()
    if damage=='missing_prediction':p=p.iloc[1:]
    if damage=='duplicate_prediction':p=pd.concat([p,p.iloc[:1]],ignore_index=True)
    if damage=='reordered_prediction':p=p.iloc[::-1]
    if damage=='wrong_date':p.loc[0,'target_date']='2023-02-01'
    if damage=='wrong_origin':p.loc[0,'forecast_origin']='2022-12-30'
    if damage=='missing_seed':p=p[p.seed!=456]
    if damage=='wrong_run':p.loc[0,'run_id']='other'
    if damage=='wrong_model':p.loc[0,'model_version']='other'
    if damage=='wrong_protocol':p.loc[0,'protocol_sha256']='0'*64
    if damage=='wrong_currency':p.loc[0,'currency']='VND'
    if damage=='wrong_scope':p.loc[0,'scope']='test'
    if damage=='wrong_dataset':p.loc[0,'dataset_version']='other'
    if damage=='nan':p.loc[0,'predicted_price']=float('nan')
    if damage=='infinite':p.loc[0,'predicted_price']=float('inf')
    if damage=='noninteger_horizon':p['horizon_step']=p.horizon_step.astype(float);p.loc[0,'horizon_step']=1.5
    if damage=='missing_actual_horizon':a=a.drop(a[a.forecast_length==5].index[0])
    if damage=='duplicate_actual':a=pd.concat([a,a.iloc[:1]],ignore_index=True)
    if damage=='mixed_actual_split':a.loc[0,'split']='test'
    if damage=='missing_mode':p=p[p.forecast_length==1];a=a[a.forecast_length==1]
    if damage=='baseline_seed':p.loc[p.method=='persistence','seed']=42
    if damage=='baseline_run':p.loc[p.method=='persistence','run_id']='fake'
    with pytest.raises(ValueError):evaluate_forecast_records(p,a,protocol=protocol)


def test_full_test_cannot_be_called_on_validation_rows():
    p,a,protocol=fixture();p['scope']='test';a['split']='test'
    with pytest.raises(ValueError):evaluate_forecast_records(p,a,protocol=protocol,split='test')


def test_metric_overflow_rejected():
    p,a,protocol=fixture();p.loc[0,'predicted_price']=1e308
    with pytest.raises(ValueError,match='overflow'):evaluate_forecast_records(p,a,protocol=protocol)


def test_boolean_mode_rejected():
    p,a,protocol=fixture()
    with pytest.raises(ValueError):evaluate_forecast_records(p,a,protocol=protocol,forecast_lengths=(True,5))


@pytest.mark.parametrize('date_value',['2023-01-99','2023-1-03',20230103])
def test_malformed_dates_rejected(date_value):
    p,a,protocol=fixture();p['target_date']=p.target_date.astype(object);p.loc[0,'target_date']=date_value
    with pytest.raises(ValueError):evaluate_forecast_records(p,a,protocol=protocol)


def test_explicit_single_mode_request():
    p,a,protocol=fixture()
    result=evaluate_forecast_records(p[p.forecast_length==1],a[a.forecast_length==1],protocol=protocol,forecast_lengths=(1,))
    assert len(result['metrics'])==7 and len(result['aggregates'])==2


def synthetic_test_fixture():
    p,a,protocol=fixture()
    mapping=dict(zip(pd.bdate_range('2023-01-02',periods=7).strftime('%Y-%m-%d'),
                     pd.bdate_range('2024-01-02',periods=7).strftime('%Y-%m-%d')))
    for frame in (p,a):
        for key in ['forecast_origin','target_date']:frame[key]=frame[key].map(mapping)
        frame['sample_id']=[f'fixture:lb30:f{h}:{o}' for h,o in zip(frame.forecast_length,frame.forecast_origin)]
    p['scope']='test';a['split']='test'
    for h in (1,5):
        cohort=[]
        for sample,rows in a[a.forecast_length==h].groupby('sample_id',sort=False):
            cohort.append(dict(sample_id=sample,forecast_origin=rows.forecast_origin.iloc[0],target_dates=rows.target_date.tolist()))
        protocol['semantic']['cohorts'].append(dict(forecast_length=h,samples=2,ordered_keys_sha256=digest(cohort)))
    protocol['semantic_sha256']=digest(protocol['semantic']);p['protocol_sha256']=protocol['semantic_sha256']
    return p,a,protocol


def test_synthetic_full_cohort_acceptance_not_real_stock_test():
    p,a,protocol=synthetic_test_fixture()
    result=evaluate_forecast_records(p,a,protocol=protocol,split='test')
    assert len(result['metrics'])==31 and (result['metrics'].range_kind=='official_full_set').all()


@pytest.mark.parametrize('damage',['count','keys'])
def test_synthetic_wrong_locked_cohort_rejected(damage):
    p,a,protocol=synthetic_test_fixture()
    if damage=='count':protocol['semantic']['cohorts'][0]['samples']=1
    else:protocol['semantic']['cohorts'][0]['ordered_keys_sha256']='0'*64
    protocol['semantic_sha256']=digest(protocol['semantic']);p['protocol_sha256']=protocol['semantic_sha256']
    with pytest.raises(ValueError,match='cohort differs'):evaluate_forecast_records(p,a,protocol=protocol,split='test')


def test_matching_partial_validation_cannot_claim_full_set():
    p,a,protocol=fixture();sample=a[a.forecast_length==1].sample_id.iloc[0]
    p=p[p.sample_id!=sample];a=a[a.sample_id!=sample]
    with pytest.raises(ValueError,match='cohort differs'):evaluate_forecast_records(p,a,protocol=protocol)


def test_validation_requires_external_cohort_reference():
    p,a,protocol=fixture()
    with pytest.raises(ValueError,match='independently accepted'):_evaluate(p,a,protocol=protocol)


def test_validation_source_hash_mismatch_rejected(tmp_path):
    p,a,protocol=fixture()
    protocol['semantic']['cohorts']=[dict(forecast_length=1,prepared_id='fixture')]
    name='data/prepared/fixture/f1_val_inputs.json'
    path=tmp_path/name;path.parent.mkdir(parents=True);path.write_text('[]')
    protocol['semantic']['artifacts_sha256']={name:'0'*64}
    with pytest.raises(ValueError,match='checksum'):load_validation_cohorts(tmp_path,protocol)
