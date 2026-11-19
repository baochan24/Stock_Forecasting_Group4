"""Synthetic artifacts for downstream contract and provenance checks."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from backend.data.validation.standard_output import inspect_standard_output
from backend.data.validation.validator import compute_sha256, EXPECTED_VALIDATED_COLUMNS


class TestStandardOutput(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.paths=[self.root/name for name in ['raw.csv','meta.json','val.csv','report.json','quality.json']]
        self.raw,self.meta,self.val,self.report,self.quality=self.paths
        pd.DataFrame({'date':['2015-01-02','2015-01-05'],'Adj Close':[24.1,23.5]}).to_csv(self.raw,index=False)
        pd.DataFrame({'date':['2015-01-02','2015-01-05'],'ticker':['AAPL']*2,'adjusted_close':[24.1,23.5],'dataset_version':['fixture']*2}).to_csv(self.val,index=False)
        self.meta.write_text(json.dumps({'row_count':2}),encoding='utf-8')
        self.r={'passed':True,'dataset_version':'fixture','provenance':{'passed':True},'raw_sha256':compute_sha256(self.raw),'source_metadata_sha256':compute_sha256(self.meta),'validated_sha256':compute_sha256(self.val),'validated_file':'val.csv','validated_columns':EXPECTED_VALIDATED_COLUMNS,'row_count':2}
        self.q={'passed':True,'dataset_version':'fixture','raw_sha256':compute_sha256(self.raw),'source_metadata_sha256':compute_sha256(self.meta)}
        self.save_reports()

    def save_reports(self):
        self.report.write_text(json.dumps(self.r),encoding='utf-8')
        self.quality.write_text(json.dumps(self.q),encoding='utf-8')

    def inspect(self):
        # Source metadata validator has its own tests; isolate the output contract here.
        with patch('backend.data.validation.standard_output.inspect_snapshot_provenance',return_value={'passed':True}):
            return inspect_standard_output(*self.paths,'fixture',self.root)

    def test_valid_output(self): self.assertTrue(self.inspect()['passed'])

    def test_wrong_hash_or_stale_quality_rejected(self):
        self.r['validated_sha256']='0'*64;self.save_reports()
        self.assertIn('validated_hash',self.inspect()['errors'])
        self.q['raw_sha256']='0'*64;self.save_reports()
        self.assertIn('quality_passed_for_same_snapshot',self.inspect()['errors'])

    def test_wrong_rows_even_with_updated_hash_rejected(self):
        for column,value in [('adjusted_close',99.),('ticker','MSFT'),('dataset_version','wrong'),('date','2015-01-06')]:
            with self.subTest(column=column):
                original=self.val.read_bytes()
                frame=pd.read_csv(self.val);frame.loc[0,column]=value;frame.to_csv(self.val,index=False)
                self.r['validated_sha256']=compute_sha256(self.val);self.save_reports()
                self.assertFalse(self.inspect()['passed'])
                self.val.write_bytes(original)

    def test_extra_column_rejected(self):
        frame=pd.read_csv(self.val);frame['extra']=1;frame.to_csv(self.val,index=False)
        self.r['validated_sha256']=compute_sha256(self.val);self.save_reports()
        self.assertIn('exact_four_column_schema',self.inspect()['errors'])

if __name__=='__main__':unittest.main()
