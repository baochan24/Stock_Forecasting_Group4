"""Tamper tests on disposable copies of the actual handoff ZIP; originals stay unchanged."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.verify_tv1_handoff import verify


class TestHandoffIntegrity(unittest.TestCase):
    def setUp(self):
        version=os.environ.get('TV1_DATASET_VERSION')
        if not version:
            self.skipTest('Set TV1_DATASET_VERSION for handoff integration tests.')
        receipt=json.loads(Path(f'data/metadata/aapl_handoff_{version}_complete.json').read_text(encoding='utf-8'))
        self.original=Path(receipt['archive'])
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.archive=Path(self.temp.name)/'copy.zip'
        self.archive.write_bytes(self.original.read_bytes())
        self.checksum=self.archive.with_suffix('.sha256')
        self.sign()

    def sign(self):
        self.checksum.write_text(hashlib.sha256(self.archive.read_bytes()).hexdigest(),encoding='utf-8')

    def rewrite(self, mutate):
        with zipfile.ZipFile(self.archive) as bundle:
            files={name:bundle.read(name) for name in bundle.namelist()}
        mutate(files)
        with zipfile.ZipFile(self.archive,'w') as bundle:
            for name,data in files.items():bundle.writestr(name,data)
        self.sign()

    def test_original_package_passes(self):
        self.assertTrue(verify(self.archive,self.checksum)['passed'])

    def test_changed_zip_rejected_by_checksum(self):
        self.archive.write_bytes(self.archive.read_bytes()+b'tamper')
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):verify(self.archive,self.checksum)

    def test_wrong_checksum_rejected(self):
        self.checksum.write_text('0'*64,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):verify(self.archive,self.checksum)

    def test_changed_member_rejected_even_with_new_zip_checksum(self):
        def mutate(files):
            path=next(name for name in files if name.startswith('data/validated/'))
            files[path]+=b'\n'
        self.rewrite(mutate)
        with self.assertRaisesRegex(ValueError,'hash/size mismatch'):verify(self.archive,self.checksum)

    def test_missing_member_rejected(self):
        def mutate(files):del files[next(name for name in files if name.startswith('data/raw/'))]
        self.rewrite(mutate)
        with self.assertRaisesRegex(ValueError,'membership mismatch'):verify(self.archive,self.checksum)

    def test_unsafe_member_rejected(self):
        self.rewrite(lambda files:files.update({'../escape.txt':b'unsafe'}))
        with self.assertRaisesRegex(ValueError,'Unsafe archive path'):verify(self.archive,self.checksum)

if __name__=='__main__':unittest.main()
