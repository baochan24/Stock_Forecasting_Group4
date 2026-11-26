"""TV2→CPU float64 model boundary; no training loop or model selection."""
from copy import deepcopy
from unittest.mock import patch
import numpy as np
import pytest
import torch
from sklearn.preprocessing import StandardScaler
from backend.data.preparation.windows import create_one_step_windows,create_five_step_windows
from backend.data.preparation.tensors import make_lstm_inputs,make_lstm_training_batch
from backend.data.transforms.scaling import inverse_scale


@pytest.mark.parametrize("h",[1,5])
def test_adapter_identity_precision_and_no_mutation(tv2_source,h):
    data,scaler = tv2_source
    create = create_one_step_windows if h == 1 else create_five_step_windows
    batch = create(data,scaler)["splits"]["val"]
    X,y = batch["X"].copy(),batch["y"].copy()
    with patch.object(StandardScaler,"fit",side_effect=AssertionError("no fit")),patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("no fit")):
        packed = make_lstm_training_batch(batch,scaler,dataset_version="fixture",forecast_length=h)
    assert packed["sample_ids"] == [r["sample_id"] for r in batch["inputs"]]
    assert packed["X"].dtype == packed["y"].dtype == torch.float64
    assert packed["X"].device.type == packed["y"].device.type == "cpu"
    np.testing.assert_array_equal(packed["X"].numpy(),X)
    np.testing.assert_array_equal(packed["y"].numpy(),y)
    np.testing.assert_allclose(inverse_scale(packed["y"].numpy(),scaler),np.stack([r["target_values"] for r in batch["targets"]]),rtol=1e-12,atol=1e-12)
    packed["X"][0,0,0] = 999
    np.testing.assert_array_equal(batch["X"],X)
    np.testing.assert_array_equal(batch["y"],y)


@pytest.mark.parametrize("h",[1,5])
def test_input_only_adapter_cannot_receive_targets(tv2_source,h):
    data,scaler = tv2_source
    batch = (create_one_step_windows if h == 1 else create_five_step_windows)(data,scaler)["splits"]["val"]
    expected = make_lstm_training_batch(batch,scaler,dataset_version="fixture",forecast_length=h)["X"]
    batch.pop("targets"); batch.pop("y")
    packed = make_lstm_inputs(batch["inputs"],scaler,dataset_version="fixture",forecast_length=h)
    assert "y" not in packed and "targets" not in packed
    torch.testing.assert_close(packed["X"],expected,rtol=0,atol=0)
    bad = deepcopy(batch["inputs"]); bad[0]["target_values"] = []
    with pytest.raises(ValueError): make_lstm_inputs(bad,scaler,dataset_version="fixture",forecast_length=h)


@pytest.mark.parametrize("h",[1,5])
def test_bad_identity_shape_pairing_or_scaled_values_rejected(tv2_source,h):
    data,scaler = tv2_source
    batch = (create_one_step_windows if h == 1 else create_five_step_windows)(data,scaler)["splits"]["val"]
    with pytest.raises(ValueError): make_lstm_inputs(batch["inputs"],scaler,dataset_version="wrong",forecast_length=h)
    with pytest.raises(ValueError): make_lstm_inputs(batch["inputs"],scaler,dataset_version="fixture",forecast_length=5 if h == 1 else 1)
    mutations = [lambda b:b["targets"][0].update(sample_id="wrong"),lambda b:b.update(y=b["y"].ravel()),
                 lambda b:b["X"].__setitem__((0,0,0),99.),lambda b:b["y"].__setitem__((0,0),np.nan),
                 lambda b:b.update(num_samples=999)]
    for mutate in mutations:
        bad = deepcopy(batch); mutate(bad)
        with pytest.raises(ValueError): make_lstm_training_batch(bad,scaler,dataset_version="fixture",forecast_length=h)


@pytest.mark.parametrize("h",[1,5])
def test_corrupt_target_dates_horizon_or_raw_price_rejected(tv2_source,h):
    data,scaler = tv2_source
    batch = (create_one_step_windows if h == 1 else create_five_step_windows)(data,scaler)["splits"]["val"]
    for field,value in [("target_dates",["2022-01-01"]*h),("horizon_step",[99]*h),("target_values",np.zeros(h))]:
        bad = deepcopy(batch); bad["targets"][0][field] = value
        with pytest.raises(ValueError): make_lstm_training_batch(bad,scaler,dataset_version="fixture",forecast_length=h)
