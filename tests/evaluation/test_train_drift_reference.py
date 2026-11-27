from copy import deepcopy
import numpy as np
import pytest
from backend.error_analysis.train_drift_reference import estimate_train_change,predict_train_change


def records(h=1):
    inputs=[dict(sample_id=str(i),dataset_version='fixture',forecast_length=h,forecast_origin='2021-12-20',input_values=[[100.]]*30) for i in range(2)]
    targets=[dict(sample_id=str(i),split='train',target_dates=[f'2021-12-{21+k}' for k in range(h)],target_values=[100.+i+k+1 for k in range(h)]) for i in range(2)]
    return inputs,targets


@pytest.mark.parametrize('h',[1,5])
def test_train_mean_by_horizon_and_input_only_prediction(h):
    x,y=records(h);r=estimate_train_change(x,y,dataset_version='fixture',train_last_date='2021-12-31')
    np.testing.assert_array_equal(r['delta_usd'],np.arange(1.5,h+1.5))
    raw=np.full((3,30,1),200.);copy=raw.copy()
    np.testing.assert_array_equal(predict_train_change(raw,r),np.tile(200.+np.arange(1.5,h+1.5),(3,1)))
    np.testing.assert_array_equal(raw,copy)


@pytest.mark.parametrize('change',['val','future','version','duplicate'])
def test_reject_leakage_and_pair_errors(change):
    x,y=records();x=deepcopy(x);y=deepcopy(y)
    if change=='val':y[0]['split']='val'
    if change=='future':y[0]['target_dates']=['2022-01-03']
    if change=='version':x[0]['dataset_version']='wrong'
    if change=='duplicate':x[1]['sample_id']=y[1]['sample_id']='0'
    with pytest.raises(ValueError):estimate_train_change(x,y,dataset_version='fixture',train_last_date='2021-12-31')
