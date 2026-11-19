"""Synthetic fixtures only; do not require downloaded datasets."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from backend.data.validation.provenance import inspect_snapshot_provenance
from backend.data.validation.validator import compute_sha256


class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root / 'raw.csv'
        self.raw.write_text('date,Adj Close\n2015-01-02,24.1\n2015-01-05,23.5\n', encoding='utf-8')
        self.meta = dict(dataset_version='fixture', ticker='AAPL', currency='USD', source='Yahoo Finance (yfinance)', yfinance_version='fixture_version', requested_start_date='2015-01-01', requested_end_date='2025-12-31', downloaded_at_utc='2026-11-19T14:13:03+00:00', adjustment_policy='auto_adjust=False; Adj Close', point_in_time_limitation='Synthetic fixture: retrospective adjustment declared', raw_file='raw.csv', raw_sha256=compute_sha256(self.raw), row_count=2, columns=['date','Adj Close'], actual_first_date='2015-01-02', actual_last_date='2015-01-05')

    def inspect(self, meta):
        return inspect_snapshot_provenance(self.raw, meta, 'fixture', self.root)

    def test_consistent_metadata(self):
        self.assertTrue(self.inspect(self.meta)['passed'])

    def test_mismatched_fields_rejected(self):
        changes = dict(dataset_version='wrong', ticker='MSFT', currency='VND', source='other', requested_start_date='2016-01-01', requested_end_date='2024-12-31', downloaded_at_utc='2026-11-19', adjustment_policy='auto_adjust=True', point_in_time_limitation='', raw_file='other.csv', raw_sha256='0'*64, row_count=3, columns=['wrong'], actual_first_date='2015-01-03')
        for field, value in changes.items():
            with self.subTest(field=field):
                meta = deepcopy(self.meta)
                meta[field] = value
                self.assertFalse(self.inspect(meta)['passed'])

    def test_missing_fields_rejected(self):
        for field in self.meta:
            with self.subTest(field=field):
                meta = deepcopy(self.meta)
                del meta[field]
                self.assertFalse(self.inspect(meta)['passed'])

    def test_modified_raw_rejected(self):
        with self.raw.open('a', encoding='utf-8') as stream:
            stream.write('2015-01-06,23.6\n')
        self.assertIn('raw_SHA256', self.inspect(self.meta)['errors'])

if __name__ == '__main__':
    unittest.main()
