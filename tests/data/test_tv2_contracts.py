"""Contract regression tests with synthetic sessions, not a full calendar."""
from copy import deepcopy
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.data.preparation.windows import create_one_step_windows, create_five_step_windows
from backend.data.preparation.contracts import validate_window_result, build_inference_inputs, validate_forecast_input


class ContractTests(unittest.TestCase):
    def setUp(self):
        dates = (pd.bdate_range("2022-11-01",periods=40).strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2023-12-01",periods=10).strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2024-01-02",periods=10).strftime("%Y-%m-%d").tolist())
        self.data = pd.DataFrame({"date":dates,"ticker":"AAPL","adjusted_close":np.arange(1.,61.),"dataset_version":"fixture"})
        self.scaler = StandardScaler().fit(np.arange(1.,41.).reshape(-1,1))

    def test_both_modes_validate_and_ids_are_disjoint(self):
        ids = []
        for create in [create_one_step_windows,create_five_step_windows]:
            result = create(self.data,self.scaler)
            check = validate_window_result(result,self.data,self.scaler)
            self.assertTrue(check["passed"])
            ids += [x["sample_id"] for b in result["splits"].values() for x in b["inputs"]]
        self.assertEqual(len(ids),len(set(ids)))

    def test_inference_needs_no_targets_and_returns_independent_copy(self):
        result = create_five_step_windows(self.data,self.scaler)
        batch = result["splits"]["val"]
        expected = batch["X"].copy()
        batch.pop("targets")
        batch.pop("y")
        with patch.object(StandardScaler,"fit",side_effect=AssertionError("no fit")),patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("no fit")):
            packed = build_inference_inputs(batch["inputs"],self.scaler)
        self.assertEqual(set(packed),{"inputs","X"})
        np.testing.assert_array_equal(packed["X"],expected)
        packed["inputs"][0]["input_values"][:] = 999
        self.assertNotEqual(batch["inputs"][0]["input_values"][0,0],999)

    def test_input_injection_and_mixed_batches_rejected(self):
        inputs = create_one_step_windows(self.data,self.scaler)["splits"]["val"]["inputs"]
        for field in ["target_dates","target_values","y","split"]:
            bad = deepcopy(inputs[0]); bad[field] = []
            with self.subTest(field=field),self.assertRaises(ValueError): validate_forecast_input(bad)
        five = create_five_step_windows(self.data,self.scaler)["splits"]["val"]["inputs"][0]
        for batch in [[],[inputs[0],inputs[0]],[inputs[0],five]]:
            with self.assertRaises(ValueError): build_inference_inputs(batch,self.scaler)

    def test_corrupt_metadata_dates_shapes_and_pairing_rejected(self):
        original = create_five_step_windows(self.data,self.scaler)
        mutations = [
            lambda b:b["inputs"][0].update(sample_id="wrong"),
            lambda b:b["inputs"][0].update(dataset_version="wrong"),
            lambda b:b["inputs"][0].update(forecast_origin="2022-01-01"),
            lambda b:b["targets"][0].update(sample_id="wrong"),
            lambda b:b["targets"][0].update(horizon_step=[5,4,3,2,1]),
            lambda b:b["targets"][0].update(split="test"),
            lambda b:b["targets"][0].update(target_dates=["2023-12-01"]*5),
            lambda b:b.update(X=b["X"].astype(np.float32)),
            lambda b:b.update(y=b["y"][:,:1]),
            lambda b:b["X"].__setitem__((0,0,0),99.),
            lambda b:b["targets"][0]["target_values"].__setitem__(0,99.),
            lambda b:b.update(target_indices=b["target_indices"][::-1]),
            lambda b:b.update(num_samples=999),
        ]
        for index, mutate in enumerate(mutations):
            result = deepcopy(original)
            mutate(result["splits"]["val"])
            with self.subTest(case=index),self.assertRaises(ValueError): validate_window_result(result,self.data,self.scaler)

    def test_missing_input_fields_or_boolean_config_rejected(self):
        record = create_one_step_windows(self.data,self.scaler)["splits"]["val"]["inputs"][0]
        for field in list(record):
            bad = deepcopy(record); bad.pop(field)
            with self.subTest(field=field),self.assertRaises(ValueError): validate_forecast_input(bad)
        bad = deepcopy(record); bad["forecast_length"] = True
        with self.assertRaises(ValueError): validate_forecast_input(bad)


if __name__ == "__main__": unittest.main()
