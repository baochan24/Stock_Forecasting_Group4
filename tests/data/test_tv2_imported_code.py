"""Synthetic acceptance checks for imported TV2 helpers, not full TV2 approval."""

import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import NotFittedError

from backend.data.preparation.preparation import fit_scaler, split_data
from backend.data.transforms.scaling import inverse_scale, scale


class ImportedTV2Tests(unittest.TestCase):
    def test_invalid_train_arrays_rejected(self):
        for values in [[], [np.nan], [np.inf], [-1], [0], [[1, 2]], [[[1]]], ["12"], [True], [1j]]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                fit_scaler(values)

    def test_invalid_transform_inputs_and_scalers(self):
        scaler = fit_scaler([10, 20, 30])
        for operation in [scale, inverse_scale]:
            for values in [[], [np.nan], [np.inf], ["12"], [1j], np.zeros((1,1,1,1)), 1.0]:
                with self.subTest(operation=operation.__name__, values=str(values)), self.assertRaises(ValueError):
                    operation(values, scaler)
            with self.assertRaises(NotFittedError):
                operation([1.0], StandardScaler())
            with self.assertRaises(TypeError):
                operation([1.0], None)
            with self.assertRaises(ValueError):
                operation([1.0], StandardScaler().fit([[1, 2], [3, 4]]))

    def test_split_sorts_and_preserves_price_date_alignment(self):
        frame = pd.DataFrame({"date": ["2024-01-02", "2015-01-02", "2023-01-03"],
                              "ticker": ["AAPL"] * 3, "adjusted_close": [30., 10., 20.], "dataset_version": ["fixture"] * 3})
        with patch("backend.data.preparation.preparation.pd.read_csv", return_value=frame):
            splits = split_data("synthetic.csv")
        for name, date, price in [("train", "2015-01-02", 10), ("val", "2023-01-03", 20), ("test", "2024-01-02", 30)]:
            self.assertEqual(splits[name]["dates"], [date])
            self.assertEqual(splits[name]["dataset_version"], "fixture")
            np.testing.assert_array_equal(splits[name]["prices"], [[price]])

    def test_invalid_dataset_rejected(self):
        base = pd.DataFrame({"date": ["2015-01-02", "2023-01-03", "2024-01-02"],
                             "ticker": ["AAPL"] * 3, "adjusted_close": [10., 20., 30.], "dataset_version": ["fixture"] * 3})
        cases = [base.drop(columns="ticker"), base.drop(columns="dataset_version"), base.iloc[:0], base.iloc[:2], pd.concat([base, base.iloc[:1]])]
        for col, value in [("date", None), ("date", "2023-02-30"), ("date", "2023-1-3"),
                           ("date", "2014-01-02"), ("ticker", "MSFT"), ("dataset_version", "other"), ("dataset_version", None), ("dataset_version", ""),
                           ("adjusted_close", np.inf), ("adjusted_close", np.nan), ("adjusted_close", -1.)]:
            frame = base.copy()
            frame.loc[0, col] = value
            cases.append(frame)
        for i, frame in enumerate(cases):
            with self.subTest(case=i), patch("backend.data.preparation.preparation.pd.read_csv", return_value=frame), self.assertRaises(ValueError):
                split_data("synthetic.csv")

    def test_future_transform_does_not_refit_training_scaler(self):
        train = np.array([10.0, 20.0, 30.0]).reshape(-1, 1)
        scaler = fit_scaler(train)
        self.assertAlmostEqual(float(scaler.mean_[0]), 20.0)
        mean, variance = scaler.mean_.copy(), scaler.var_.copy()
        count = int(scaler.n_samples_seen_)
        past = scale(train, scaler).copy()
        scale(np.array([[1000000.0], [2000000.0]]), scaler)
        np.testing.assert_array_equal(scaler.mean_, mean)
        np.testing.assert_array_equal(scaler.var_, variance)
        self.assertEqual(int(scaler.n_samples_seen_), count)
        np.testing.assert_array_equal(scale(train, scaler), past)

    def test_roundtrip_model_shapes(self):
        scaler = fit_scaler(np.array([10.0, 20.0, 30.0]))
        for shape in [(2, 30, 1), (2, 1), (2, 5)]:
            with self.subTest(shape=shape):
                original = np.linspace(5.0, 300.0, num=np.prod(shape), dtype=np.float32).reshape(shape)
                scaled = scale(original, scaler)
                restored = inverse_scale(scaled, scaler)
                self.assertEqual(scaled.shape, shape)
                self.assertEqual(restored.shape, shape)
                np.testing.assert_allclose(restored, original, rtol=1e-6, atol=1e-5)


if __name__ == "__main__":
    unittest.main()
