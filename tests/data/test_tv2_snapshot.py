"""Synthetic artifacts; only calendar completeness is mocked for 3-row fixtures."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.preparation import split_data
from backend.data.validation.validator import compute_sha256


class TV2SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.version = "fixture"
        self.paths = {
            "raw": self.root / "data/raw/aapl_raw_fixture.csv",
            "metadata": self.root / "data/metadata/aapl_metadata_fixture.json",
            "validated": self.root / "data/validated/aapl_validated_fixture.csv",
            "validation_report": self.root / "data/metadata/aapl_validation_report_fixture.json",
            "quality_audit": self.root / "data/metadata/aapl_quality_audit_fixture.json",
        }
        for path in self.paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        dates = ["2015-01-02", "2023-01-03", "2024-01-02"]
        raw = pd.DataFrame({"date": dates, "Adj Close": [10., 20., 30.]})
        val = pd.DataFrame({"date": dates, "ticker": ["AAPL"]*3,
                            "adjusted_close": [10., 20., 30.], "dataset_version": ["fixture"]*3})
        raw.to_csv(self.paths["raw"], index=False)
        val.to_csv(self.paths["validated"], index=False)
        meta = dict(dataset_version="fixture", ticker="AAPL", currency="USD",
                    source="Yahoo Finance (yfinance)", yfinance_version="fixture",
                    requested_start_date="2015-01-01", requested_end_date="2025-12-31",
                    downloaded_at_utc="2026-11-19T14:13:03+00:00",
                    adjustment_policy="auto_adjust=False; Adj Close", point_in_time_limitation="Synthetic fixture",
                    raw_file="data/raw/aapl_raw_fixture.csv", raw_sha256=compute_sha256(self.paths["raw"]),
                    row_count=3, columns=list(raw.columns), actual_first_date=dates[0], actual_last_date=dates[-1])
        self.write("metadata", meta)
        common = dict(passed=True, dataset_version="fixture", raw_sha256=compute_sha256(self.paths["raw"]),
                      source_metadata_sha256=compute_sha256(self.paths["metadata"]))
        self.write("quality_audit", common)
        self.report = dict(**common, provenance={"passed": True}, row_count=3,
                           validated_sha256=compute_sha256(self.paths["validated"]),
                           validated_file="data/validated/aapl_validated_fixture.csv", validated_columns=list(val.columns))
        self.write("validation_report", self.report)

    def write(self, key, value):
        self.paths[key].write_text(json.dumps(value), encoding="utf-8")

    def load(self):
        with patch("backend.data.preparation.snapshot.inspect_raw_dataframe", return_value=({"passed": True}, None)):
            return load_tv1_snapshot(self.root, "fixture")

    def test_accept_preserves_version_rows_prices_and_artifacts(self):
        before = {k: compute_sha256(p) for k,p in self.paths.items()}
        accepted = self.load()
        self.assertTrue(accepted["acceptance"]["passed"])
        self.assertEqual(accepted["data"].adjusted_close.tolist(), [10.,20.,30.])
        splits = split_data(accepted["data"])
        self.assertTrue(all(x["dataset_version"] == "fixture" for x in splits.values()))
        self.assertEqual(before, {k: compute_sha256(p) for k,p in self.paths.items()})

    def test_changed_validated_file_rejected(self):
        with self.paths["validated"].open("a") as stream:
            stream.write("2025-01-02,AAPL,40,fixture\n")
        with self.assertRaises(ValueError): self.load()

    def test_metadata_ticker_currency_or_policy_rejected(self):
        original = json.loads(self.paths["metadata"].read_text())
        for key, value in [("ticker","MSFT"),("currency","VND"),("adjustment_policy","auto_adjust=True")]:
            with self.subTest(key=key):
                self.write("metadata", dict(original, **{key:value}))
                with self.assertRaises(ValueError): self.load()

    def test_wrong_version_even_with_updated_output_hash_rejected(self):
        frame = pd.read_csv(self.paths["validated"])
        frame.loc[0,"dataset_version"] = "wrong"
        frame.to_csv(self.paths["validated"], index=False)
        self.report["validated_sha256"] = compute_sha256(self.paths["validated"])
        self.write("validation_report", self.report)
        with self.assertRaises(ValueError): self.load()

    def test_missing_artifact_or_unsafe_version_rejected(self):
        with self.assertRaises(ValueError): load_tv1_snapshot(self.root, "../fixture")
        self.paths["quality_audit"].unlink()
        with self.assertRaises(FileNotFoundError): self.load()

    def test_fresh_quality_failure_rejected(self):
        with patch("backend.data.preparation.snapshot.inspect_raw_dataframe", return_value=({"passed":False,"errors":["missing session"]},None)):
            with self.assertRaisesRegex(ValueError, "missing session"):
                load_tv1_snapshot(self.root, "fixture")


if __name__ == "__main__":
    unittest.main()
