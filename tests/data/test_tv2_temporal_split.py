"""Synthetic target dates; no model evaluation or price-driven split selection."""
import unittest
import numpy as np
import pandas as pd
from backend.data.preparation.preparation import create_split_plan, target_split


class TemporalSplitTests(unittest.TestCase):
    def test_single_target_boundaries(self):
        for date, expected in [("2015-01-02","train"),("2022-12-30","train"),
                               ("2023-01-03","val"),("2023-12-29","val"),
                               ("2024-01-02","test"),("2025-12-31","test")]:
            with self.subTest(date=date): self.assertEqual(target_split([date]), expected)

    def test_five_targets_crossing_split_are_ineligible(self):
        self.assertIsNone(target_split(["2022-12-28","2022-12-29","2022-12-30","2023-01-03","2023-01-04"]))
        self.assertIsNone(target_split(["2023-12-27","2023-12-28","2023-12-29","2024-01-02","2024-01-03"]))
        self.assertEqual(target_split(["2023-01-03","2023-01-04","2023-01-05","2023-01-06","2023-01-09"]), "val")

    def test_invalid_targets_rejected(self):
        for values in [[], ["2014-12-31"], ["2026-01-02"], ["2023-02-30"], [None],
                       ["2023-1-3"], ["2023-01-03"]*5,
                       ["2023-01-09","2023-01-06","2023-01-05","2023-01-04","2023-01-03"]]:
            with self.subTest(values=values), self.assertRaises(ValueError): target_split(values)

    def test_plan_preserves_history_alignment_and_input(self):
        dates = ["2022-12-29","2022-12-30","2023-01-03","2023-12-29","2024-01-02"]
        frame = pd.DataFrame({"date": dates, "ticker": "AAPL", "adjusted_close": [1.,2.,3.,4.,5.], "dataset_version": "fixture"})
        shuffled = frame.iloc[::-1].copy()
        before = shuffled.copy(deep=True)
        plan = create_split_plan(shuffled)
        pd.testing.assert_frame_equal(shuffled, before)
        pd.testing.assert_frame_equal(plan["data"], frame)
        np.testing.assert_array_equal(plan["target_indices"]["val"], [2,3])
        np.testing.assert_array_equal(plan["target_indices"]["test"], [4])
        self.assertEqual(plan["data"].iloc[plan["target_indices"]["val"][0]-1].date, "2022-12-30")
        self.assertEqual(plan["data"].iloc[plan["target_indices"]["test"][0]-1].date, "2023-12-29")

    def test_split_is_independent_of_price_values(self):
        dates = ["2022-12-30","2023-01-03","2024-01-02"]
        frame = pd.DataFrame({"date": dates,"ticker":"AAPL","adjusted_close":[1.,2.,3.],"dataset_version":"fixture"})
        first = create_split_plan(frame)
        frame.loc[1:,"adjusted_close"] = [20000.,30000.]
        second = create_split_plan(frame)
        for name in first["target_indices"]:
            np.testing.assert_array_equal(first["target_indices"][name],second["target_indices"][name])


if __name__ == "__main__": unittest.main()
