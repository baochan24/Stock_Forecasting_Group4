"""Synthetic sessions/prices for hand-checking direct multi-output windows."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.data.preparation.windows import create_five_step_windows, create_one_step_windows
from backend.data.transforms.scaling import inverse_scale


class FiveStepWindowTests(unittest.TestCase):
    def setUp(self):
        dates = (pd.bdate_range("2022-10-03","2022-12-30").strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2023-12-01","2023-12-29").strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2024-01-02","2024-01-15").strftime("%Y-%m-%d").tolist())
        self.frame = pd.DataFrame({"date":dates,"ticker":"AAPL","adjusted_close":np.arange(1.,len(dates)+1),"dataset_version":"fixture"})
        train = self.frame.loc[self.frame.date < "2023-01-01","adjusted_close"]
        self.scaler = StandardScaler().fit(train.to_numpy().reshape(-1,1))

    def test_hand_checked_five_outputs_and_all_alignment(self):
        result = create_five_step_windows(self.frame,self.scaler)
        batch = result["splits"]["train"]
        np.testing.assert_array_equal(batch["inputs"][0]["input_values"].ravel(),np.arange(1,31))
        np.testing.assert_array_equal(batch["targets"][0]["target_values"],np.arange(31,36))
        for split,batch in result["splits"].items():
            self.assertEqual(batch["X"].shape,(batch["num_samples"],30,1))
            self.assertEqual(batch["y"].shape,(batch["num_samples"],5))
            for n,(i,inp,target) in enumerate(zip(batch["target_indices"],batch["inputs"],batch["targets"])):
                self.assertEqual(target["target_dates"],self.frame.date.iloc[i:i+5].tolist())
                self.assertEqual(target["horizon_step"],[1,2,3,4,5])
                self.assertLess(inp["forecast_origin"],target["target_dates"][0])
                self.assertEqual(inp["sample_id"],target["sample_id"])
                np.testing.assert_allclose(inverse_scale(batch["y"][n],self.scaler),target["target_values"],atol=1e-12)

    def test_boundaries_and_exclusion_accounting(self):
        result = create_five_step_windows(self.frame,self.scaler)
        for split,batch in result["splits"].items():
            years = [int(date[:4]) for t in batch["targets"] for date in t["target_dates"]]
            self.assertTrue(all(2015 <= y <= 2022 if split == "train" else y == 2023 if split == "val" else 2024 <= y <= 2025 for y in years))
            self.assertEqual(batch["excluded_cross_split_targets"],0 if split == "test" else 4)
            self.assertEqual(batch["excluded_incomplete_targets"],4 if split == "test" else 0)
        val = result["splits"]["val"]
        test = result["splits"]["test"]
        self.assertEqual(val["inputs"][0]["forecast_origin"],"2022-12-30")
        self.assertEqual(test["inputs"][0]["forecast_origin"],"2023-12-29")
        self.assertEqual(test["targets"][0]["target_dates"][0],"2024-01-02")
        self.assertEqual(test["targets"][-1]["target_dates"][-1],"2024-01-15")

    def test_future_target_changes_leave_current_input_unchanged_and_ids_disjoint(self):
        with patch.object(StandardScaler,"fit",side_effect=AssertionError("no fit")),patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("no fit")):
            first = create_five_step_windows(self.frame,self.scaler)
            changed = self.frame.copy()
            changed.loc[changed.date >= "2024-01-02","adjusted_close"] *= 100
            second = create_five_step_windows(changed,self.scaler)
            one = create_one_step_windows(self.frame,self.scaler)
        np.testing.assert_array_equal(first["splits"]["test"]["X"][0],second["splits"]["test"]["X"][0])
        self.assertFalse(np.array_equal(first["splits"]["test"]["y"][0],second["splits"]["test"]["y"][0]))
        ids5 = {x["sample_id"] for b in first["splits"].values() for x in b["inputs"]}
        ids1 = {x["sample_id"] for b in one["splits"].values() for x in b["inputs"]}
        self.assertTrue(ids5.isdisjoint(ids1))

    def test_empty_five_step_targets_have_exact_shapes(self):
        tiny = self.frame.iloc[[0,-11,-1]].copy()
        result = create_five_step_windows(tiny,self.scaler)
        for batch in result["splits"].values():
            self.assertEqual(batch["X"].shape,(0,30,1))
            self.assertEqual(batch["y"].shape,(0,5))


if __name__ == "__main__": unittest.main()
