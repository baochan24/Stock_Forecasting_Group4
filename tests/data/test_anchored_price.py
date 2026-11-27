import numpy as np
import pytest
from backend.data.transforms.anchored_price import encode_history,encode_targets,decode_prices


@pytest.mark.parametrize('h',[1,5])
def test_hand_computed_roundtrip_and_translation(h):
    x=np.arange(101.,131.).reshape(1,30,1)
    y=np.arange(131.,131.+h).reshape(1,h)
    z,a=encode_history(x,10.)
    np.testing.assert_array_equal(z[0,:,0],np.arange(-29.,1.)/10.)
    d=encode_targets(y,a,10.)
    np.testing.assert_array_equal(decode_prices(d,a,10.),y)
    zz,aa=encode_history(x+200.,10.)
    np.testing.assert_array_equal(zz,z)
    np.testing.assert_array_equal(encode_targets(y+200.,aa,10.),d)
    np.testing.assert_array_equal(decode_prices(d,aa,10.),y+200.)
    np.testing.assert_array_equal(decode_prices(np.zeros((1,h)),a,10.),np.full((1,h),130.))


@pytest.mark.parametrize('bad',[0,-1,float('nan'),float('inf'),True])
def test_invalid_scale(bad):
    with pytest.raises(ValueError):encode_history(np.ones((1,30,1)),bad)


def test_reject_shape_and_future_target_contamination():
    with pytest.raises(ValueError):encode_history(np.ones((1,31,1)),1.)
    with pytest.raises(ValueError):encode_targets(np.ones((1,5)),np.ones(2),1.)
    x=np.ones((2,30,1));copy=x.copy();z,a=encode_history(x,1.)
    encode_targets(np.full((2,1),999.),a,1.)
    np.testing.assert_array_equal(x,copy)
    np.testing.assert_array_equal(z,np.zeros_like(x))
