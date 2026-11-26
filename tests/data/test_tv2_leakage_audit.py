"""Deliberately corrupt outputs to test audit detection, synthetic calendar."""
from copy import deepcopy
import unittest
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.audit.tv2_leakage import audit_temporal_windows,audit_train_statistics
from backend.data.preparation.windows import create_five_step_windows


class LeakageAuditTests(unittest.TestCase):
    def setUp(self):
        dates = (pd.bdate_range("2022-10-03",periods=50).strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2023-12-01",periods=10).strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2024-01-02",periods=10).strftime("%Y-%m-%d").tolist())
        self.data = pd.DataFrame({"date":dates,"ticker":"AAPL","adjusted_close":np.arange(1.,71.),"dataset_version":"fixture"})
        self.scaler = StandardScaler().fit(np.arange(1.,51.).reshape(-1,1))
        self.meta = {"fit_first_date":dates[0],"fit_last_date":dates[49],"fit_row_count":50,"fit_split":"train"}
        self.result = create_five_step_windows(self.data,self.scaler)

    def test_valid_outputs_and_train_moments(self):
        self.assertTrue(audit_train_statistics(self.data,self.scaler,self.meta)["passed"])
        self.assertTrue(audit_temporal_windows(self.result,self.data,self.scaler)["passed"])

    def test_scaler_fitted_on_all_data_rejected(self):
        contaminated = StandardScaler().fit(self.data.adjusted_close.to_numpy().reshape(-1,1))
        with self.assertRaises(ValueError): audit_train_statistics(self.data,contaminated,self.meta)

    def test_missing_consistently_removed_sample_rejected(self):
        batch = self.result["splits"]["val"]
        for key in ["inputs","targets","X","y","target_indices"]: batch[key] = batch[key][1:]
        batch["num_samples"] -= 1
        with self.assertRaisesRegex(ValueError,"eligible samples"): audit_temporal_windows(self.result,self.data,self.scaler)

    def test_future_input_and_wrong_exclusion_rejected(self):
        bad = deepcopy(self.result)
        sample = bad["splits"]["test"]["inputs"][0]
        sample["input_dates"][-1] = "2025-12-31"
        with self.assertRaises(ValueError): audit_temporal_windows(bad,self.data,self.scaler)
        self.result["splits"]["val"]["excluded_cross_split_targets"] = 0
        with self.assertRaisesRegex(ValueError,"exclusion"): audit_temporal_windows(self.result,self.data,self.scaler)

    def test_wrong_fit_metadata_or_reversed_source_rejected(self):
        bad = dict(self.meta,fit_last_date="2023-12-01")
        with self.assertRaises(ValueError): audit_train_statistics(self.data,self.scaler,bad)
        with self.assertRaises(ValueError): audit_temporal_windows(self.result,self.data.iloc[::-1],self.scaler)


if __name__ == "__main__": unittest.main()
