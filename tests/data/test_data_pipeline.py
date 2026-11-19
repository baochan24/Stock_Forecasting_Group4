from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

import pandas as pd

from backend.data.validation.validator import (
    EXPECTED_VALIDATED_COLUMNS,
    compute_sha256,
    inspect_raw_dataframe,
)


class TestDataValidationPipeline(unittest.TestCase):
    def test_valid_dataframe_passes(self) -> None:
        sample_df = pd.DataFrame(
            {
                "date": ["2015-01-02", "2015-01-05", "2015-01-06"],
                "Adj Close": [24.15, 23.47, 23.48],
            }
        )
        report, validated_df = inspect_raw_dataframe(sample_df, dataset_version="test_v1", start_date='2015-01-01', end_date='2015-01-06')
        self.assertTrue(report["passed"])
        self.assertEqual(list(validated_df.columns), EXPECTED_VALIDATED_COLUMNS)
        self.assertEqual(len(validated_df), 3)

    def test_duplicate_dates_rejected(self) -> None:
        dup_df = pd.DataFrame(
            {
                "date": ["2015-01-02", "2015-01-02"],
                "Adj Close": [24.15, 24.15],
            }
        )
        report, validated_df = inspect_raw_dataframe(dup_df, dataset_version="test_dup")
        self.assertFalse(report["passed"])
        self.assertEqual(report["duplicate_date_count"], 1)
        self.assertTrue(validated_df.empty)

    def test_missing_or_non_positive_price_rejected(self) -> None:
        bad_price_df = pd.DataFrame(
            {
                "date": ["2015-01-02", "2015-01-05"],
                "Adj Close": [24.15, -5.0],
            }
        )
        report, _ = inspect_raw_dataframe(bad_price_df, dataset_version="test_bad_price")
        self.assertFalse(report["passed"])
        self.assertEqual(report["non_positive_count"], 1)

    def test_generated_aapl_artifacts_integrity(self) -> None:
        """Kiểm tra bộ dữ liệu AAPL thật đã tạo trong thư mục data/."""
        version = os.environ.get('TV1_DATASET_VERSION')
        if not version:
            self.skipTest('Set TV1_DATASET_VERSION to run real-artifact integration verification.')
        raw_file = Path(f"data/raw/aapl_raw_{version}.csv")
        val_file = Path(f"data/validated/aapl_validated_{version}.csv")
        meta_file = Path(f"data/metadata/aapl_metadata_{version}.json")
        report_file = Path(f"data/metadata/aapl_validation_report_{version}.json")

        self.assertTrue(raw_file.exists(), "Thiếu file raw CSV")
        self.assertTrue(val_file.exists(), "Thiếu file validated CSV")
        self.assertTrue(meta_file.exists(), "Thiếu file metadata JSON")
        self.assertTrue(report_file.exists(), "Thiếu file validation report JSON")

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        val_report = json.loads(report_file.read_text(encoding="utf-8"))

        self.assertEqual(compute_sha256(raw_file), meta["raw_sha256"])
        self.assertEqual(compute_sha256(val_file), val_report["validated_sha256"])

        val_df = pd.read_csv(val_file)
        self.assertEqual(list(val_df.columns), EXPECTED_VALIDATED_COLUMNS)
        self.assertEqual(len(val_df), 2766)
        self.assertEqual(val_df["date"].iloc[0], "2015-01-02")
        self.assertEqual(val_df["date"].iloc[-1], "2025-12-31")
        self.assertTrue((val_df["ticker"] == "AAPL").all())


if __name__ == "__main__":
    unittest.main()
