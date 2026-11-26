"""Offline synthetic full-period pipeline; never download or modify real artifacts."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import exchange_calendars as xcals
import numpy as np
import pandas as pd

from backend.data.acquisition.downloader import download_aapl_snapshot
from backend.data.validation.validator import validate_aapl_dataset, compute_sha256


class TestPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.raw=self.root/'raw';self.meta=self.root/'meta';self.val=self.root/'val'
        dates=xcals.get_calendar('NASDAQ',start='2014-12-01',end='2026-01-31').sessions_in_range('2015-01-01','2025-12-31')
        prices=20+np.arange(len(dates))*.01
        self.synthetic=pd.DataFrame({'Adj Close':prices,'Close':prices*1.05},index=pd.DatetimeIndex(dates,name='Date'))

    def acquire(self):
        with patch('backend.data.acquisition.downloader.yf.download',return_value=self.synthetic):
            return download_aapl_snapshot('synthetic_integration',self.raw,self.meta)

    def validate(self):
        return validate_aapl_dataset('synthetic_integration',self.raw,self.val,self.meta)

    def test_download_validation_reload_and_refuse_overwrite(self):
        meta=self.acquire();report=self.validate()
        self.assertTrue(report['passed']);self.assertEqual(report['calendar']['missing_sessions'],[])
        raw=pd.read_csv(meta['raw_file']);val=pd.read_csv(report['validated_file'])
        np.testing.assert_allclose(raw['Adj Close'],val.adjusted_close,rtol=1e-12,atol=1e-12)
        self.assertEqual(raw.date.tolist(),val.date.tolist())
        self.assertTrue(val.dataset_version.eq('synthetic_integration').all())
        before=compute_sha256(Path(report['validated_file']))
        with self.assertRaises(FileExistsError):self.validate()
        self.assertEqual(before,compute_sha256(Path(report['validated_file'])))

    def test_tampered_raw_stops_before_output(self):
        meta=self.acquire();path=Path(meta['raw_file']);path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'Metadata/provenance mismatch'):self.validate()
        self.assertFalse(self.val.exists())

    def test_report_write_failure_rolls_back_and_retry_succeeds(self):
        self.acquire()
        with patch('backend.data.validation.validator.json.dump',side_effect=OSError('synthetic report write failure')):
            with self.assertRaises(OSError):self.validate()
        self.assertFalse((self.val/'aapl_validated_synthetic_integration.csv').exists())
        self.assertFalse((self.meta/'aapl_validation_report_synthetic_integration.json').exists())
        self.assertTrue(self.validate()['passed'])

    def test_wrong_ticker_stops_before_output(self):
        self.acquire();path=self.meta/'aapl_metadata_synthetic_integration.json'
        meta=json.loads(path.read_text(encoding='utf-8'));meta['ticker']='MSFT';path.write_text(json.dumps(meta),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Metadata/provenance mismatch'):self.validate()
        self.assertFalse(self.val.exists())

if __name__=='__main__':unittest.main()
