import numpy as np
import pytest
from backend.baselines.persistence import predict_persistence
from backend.evaluation.one_step import evaluate_one_step


def test_hand_calculated_metrics():
    keys=[('a','2023-01-03'),('b','2023-01-04')]
    m=evaluate_one_step([[10],[20]],[[12],[16]],target_keys=keys,prediction_keys=keys)
    assert m['sample_count']==2 and m['mae_usd']==3
    assert m['rmse_usd']==pytest.approx(np.sqrt(10))


@pytest.mark.parametrize('keys',[[('b','d'),('a','d')],[('a','d')],[('a','wrong'),('b','d')]])
def test_misalignment_rejected(keys):
    with pytest.raises(ValueError):
        evaluate_one_step([[1],[2]],[[1],[2]],target_keys=[('a','d'),('b','d')],prediction_keys=keys)


def test_duplicates_rejected():
    with pytest.raises(ValueError):
        evaluate_one_step([[1],[2]],[[1],[2]],target_keys=['a','a'],prediction_keys=['a','a'])


@pytest.mark.parametrize('pred',[[1,2],[[1,2]],[[float('nan')],[1]],[[float('inf')],[1]]])
def test_bad_predictions_rejected(pred):
    with pytest.raises(ValueError):
        evaluate_one_step([[1],[2]],pred,target_keys=['a','b'],prediction_keys=['a','b'])


@pytest.mark.parametrize('h',[1,5])
def test_persistence_last_raw_price(h):
    x=np.array([[[10.],[12.]],[[20.],[17.]]])
    before=x.copy()
    np.testing.assert_array_equal(predict_persistence(x,h),np.repeat([[12.],[17.]],h,axis=1))
    np.testing.assert_array_equal(x,before)


def test_nonfinite_persistence_rejected():
    with pytest.raises(ValueError): predict_persistence([[[float('nan')]]])
