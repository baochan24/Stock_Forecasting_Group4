"""Synthetic hand-checkable prices; no model training or full-calendar claim."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from backend.data.preparation.windows import create_one_step_windows
from backend.data.transforms.scaling import inverse_scale


class OneStepWindowTests(unittest.TestCase):
    def setUp(self):
        dates = pd.bdate_range("2022-11-01","2023-01-10").strftime("%Y-%m-%d").tolist()
        dates += ["2023-12-28","2023-12-29","2024-01-02","2024-01-03"]
        self.frame = pd.DataFrame({"date":dates,"ticker":"AAPL",
                                   "adjusted_close":np.arange(1,len(dates)+1,dtype=float),"dataset_version":"fixture"})
        train = self.frame.loc[self.frame.date < "2023-01-01","adjusted_close"]
        self.scaler = StandardScaler().fit(train.to_numpy().reshape(-1,1))

    def test_first_window_hand_checked_and_all_alignment(self):
        result = create_one_step_windows(self.frame,self.scaler)
        sample = result["splits"]["train"]
        np.testing.assert_array_equal(sample["inputs"][0]["input_values"].ravel(),np.arange(1,31))
        np.testing.assert_array_equal(sample["targets"][0]["target_values"],[31])
        for split,batch in result["splits"].items():
            self.assertEqual(batch["X"].shape,(batch["num_samples"],30,1))
            self.assertEqual(batch["y"].shape,(batch["num_samples"],1))
            for index,(inp,target) in enumerate(zip(batch["inputs"],batch["targets"])):
                self.assertEqual(inp["forecast_origin"],inp["input_dates"][-1])
                self.assertLess(inp["forecast_origin"],target["target_dates"][0])
                self.assertEqual(inp["sample_id"],target["sample_id"])
                self.assertNotIn("target_values",inp)
                self.assertEqual(target["split"],split)
                np.testing.assert_allclose(inverse_scale(batch["X"][index],self.scaler),inp["input_values"],atol=1e-12)
                np.testing.assert_allclose(inverse_scale(batch["y"][index],self.scaler),target["target_values"],atol=1e-12)

    def test_boundaries_keep_preceding_history_and_ids_unique(self):
        result = create_one_step_windows(self.frame,self.scaler)
        ids = []
        for split,batch in result["splits"].items():
            ids += [x["sample_id"] for x in batch["inputs"]]
        self.assertEqual(len(ids),len(set(ids)))
        val = result["splits"]["val"]
        test = result["splits"]["test"]
        self.assertEqual(val["targets"][0]["target_dates"],["2023-01-02"])
        self.assertEqual(val["inputs"][0]["forecast_origin"],"2022-12-30")
        self.assertEqual(test["targets"][0]["target_dates"],["2024-01-02"])
        self.assertEqual(test["inputs"][0]["forecast_origin"],"2023-12-29")
        self.assertEqual(val["excluded_insufficient_history"],0)
        self.assertEqual(test["excluded_insufficient_history"],0)

    def test_future_changes_do_not_change_past_input_or_refit(self):
        before_frame = self.frame.copy(deep=True)
        with patch.object(StandardScaler,"fit",side_effect=AssertionError("no refit")), patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("no refit")):
            first = create_one_step_windows(self.frame,self.scaler)
            changed = self.frame.copy()
            changed.loc[changed.date >= "2024-01-02","adjusted_close"] *= 100
            second = create_one_step_windows(changed,self.scaler)
        np.testing.assert_array_equal(first["splits"]["test"]["X"][0],second["splits"]["test"]["X"][0])
        self.assertNotEqual(first["splits"]["test"]["y"][0,0],second["splits"]["test"]["y"][0,0])
        pd.testing.assert_frame_equal(self.frame,before_frame)

    def test_insufficient_history_empty_shapes_and_copy_isolation(self):
        tiny = self.frame.iloc[[0,-4,-1]].copy()
        tiny.loc[:,"date"] = ["2022-12-30","2023-12-29","2024-01-03"]
        result = create_one_step_windows(tiny,self.scaler)
        for batch in result["splits"].values():
            self.assertEqual(batch["X"].shape,(0,30,1))
            self.assertEqual(batch["y"].shape,(0,1))
            self.assertEqual(batch["excluded_insufficient_history"],1)
        full = create_one_step_windows(self.frame,self.scaler)
        inputs = full["splits"]["train"]["inputs"]
        next_before = inputs[1]["input_values"].copy()
        inputs[0]["input_values"][:] = 999
        np.testing.assert_array_equal(inputs[1]["input_values"],next_before)


if __name__ == "__main__": unittest.main()
