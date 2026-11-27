"""Synthetic network responses; no live downloads or project data changes."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from backend.data.acquisition.downloader import download_aapl_snapshot, compute_sha256


class TestSnapshotVersioning(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root / 'raw'
        self.meta = self.root / 'metadata'

    def download(self, version='fixture_v1'):
        return download_aapl_snapshot(version, self.raw, self.meta)

    @patch('backend.data.acquisition.downloader.yf.download')
    def test_existing_or_partial_pair_never_downloaded_or_changed(self, network):
        for folder, name in [(self.raw,'aapl_raw_fixture_v1.csv'), (self.meta,'aapl_metadata_fixture_v1.json')]:
            with self.subTest(existing=name):
                folder.mkdir(exist_ok=True)
                target = folder / name
                target.write_bytes(b'existing snapshot')
                with self.assertRaises(FileExistsError):
                    self.download()
                self.assertEqual(target.read_bytes(), b'existing snapshot')
                network.assert_not_called()
                target.unlink()

    @patch('backend.data.acquisition.downloader.yf.download')
    def test_new_version_succeeds_then_repeat_rejected(self, network):
        network.return_value = pd.DataFrame({'Adj Close':[24.1,23.5], 'Close':[27.3,26.5]}, index=pd.DatetimeIndex(['2015-01-02','2015-01-05'], name='Date'))
        result = self.download()
        raw = Path(result['raw_file'])
        meta = self.meta / 'aapl_metadata_fixture_v1.json'
        before = (raw.read_bytes(), meta.read_bytes())
        self.assertEqual(result['raw_sha256'], compute_sha256(raw))
        self.assertEqual(json.loads(meta.read_text(encoding='utf-8')), result)
        with self.assertRaises(FileExistsError):
            self.download()
        self.assertEqual(network.call_count, 1)
        self.assertEqual(before, (raw.read_bytes(), meta.read_bytes()))
        self.download('fixture_v2')
        self.assertEqual(before, (raw.read_bytes(), meta.read_bytes()))

    @patch('backend.data.acquisition.downloader.yf.download', side_effect=RuntimeError('network failure'))
    def test_failure_removes_only_new_pair(self, network):
        self.raw.mkdir()
        old = self.raw / 'unrelated.csv'
        old.write_bytes(b'keep')
        with self.assertRaises(RuntimeError):
            self.download()
        self.assertEqual(old.read_bytes(), b'keep')
        self.assertFalse((self.raw/'aapl_raw_fixture_v1.csv').exists())
        self.assertFalse((self.meta/'aapl_metadata_fixture_v1.json').exists())

    @patch('backend.data.acquisition.downloader.yf.download')
    def test_file_created_after_precheck_is_preserved(self, network):
        original_open = Path.open
        competing = self.meta / 'aapl_metadata_fixture_v1.json'

        def create_competing_file(path, mode='r', *args, **kwargs):
            if path == competing and mode == 'x':
                with original_open(path, 'w', encoding='utf-8') as stream:
                    stream.write('concurrent owner')
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, 'open', create_competing_file):
            with self.assertRaises(FileExistsError):
                self.download()
        self.assertEqual(competing.read_text(encoding='utf-8'), 'concurrent owner')
        self.assertFalse((self.raw/'aapl_raw_fixture_v1.csv').exists())
        network.assert_not_called()

    @patch('backend.data.acquisition.downloader.yf.download')
    def test_invalid_version_rejected_before_network(self, network):
        for value in ['', '../escape', 'a/b', 'a\\b', None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.download(value)
        network.assert_not_called()

if __name__ == '__main__':
    unittest.main()
