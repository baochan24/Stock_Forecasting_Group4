"""Synthetic snapshot contract; acceptance itself is covered by snapshot tests."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from backend.artifacts.scaler import load_scaler
from backend.data.preparation.train_scaler import build_train_scaler
from backend.data.transforms.scaling import scale, inverse_scale


class TrainScalerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.frame = pd.DataFrame({"date":["2015-01-02","2022-12-30","2023-01-03","2024-01-02"],
                                   "ticker":"AAPL","adjusted_close":[10.,30.,1000.,2000.],"dataset_version":"fixture"})
        self.hashes = {k:"a"*64 for k in ["raw","metadata","validated","validation_report","quality_audit"]}

    def build(self, identifier="test"):
        accepted = {"data":self.frame.copy(),"dataset_version":"fixture","acceptance":{"passed":True,"hashes":self.hashes}}
        with patch("backend.data.preparation.train_scaler.load_tv1_snapshot",return_value=accepted):
            return build_train_scaler(self.root,"fixture",scaler_id=identifier)

    def load(self, folder, **kwargs):
        return load_scaler(folder,expected_dataset_version=kwargs.get("version","fixture"),
                           expected_source_hashes=kwargs.get("hashes",self.hashes))

    def test_fit_once_train_only_and_future_changes_do_not_affect_fit(self):
        original_fit = StandardScaler.fit
        calls = []
        def recording_fit(scaler, values, *args, **kwargs):
            calls.append(values.copy())
            return original_fit(scaler,values,*args,**kwargs)
        with patch.object(StandardScaler,"fit",recording_fit):
            first = self.build("first")
        self.assertEqual(len(calls),1)
        np.testing.assert_array_equal(calls[0],[[10.],[30.]])
        self.frame.loc[2:,"adjusted_close"] = [1e6,2e6]
        second = self.build("second")
        np.testing.assert_array_equal(first["scaler"].mean_,second["scaler"].mean_)
        np.testing.assert_array_equal(first["scaler"].var_,second["scaler"].var_)
        self.assertEqual(int(first["scaler"].n_samples_seen_),2)

    def test_reload_and_transform_never_fit_and_roundtrip(self):
        result = self.build()
        with patch.object(StandardScaler,"fit",side_effect=AssertionError("must not fit")):
            loaded, manifest = self.load(result["folder"])
            values = self.frame.adjusted_close.to_numpy()
            np.testing.assert_array_equal(scale(values,loaded),scale(values,result["scaler"]))
            np.testing.assert_allclose(inverse_scale(scale(values,loaded),loaded),values,rtol=1e-12,atol=1e-12)
        self.assertEqual(manifest["metadata"]["fit_last_date"],"2022-12-30")

    def test_id_reuse_does_not_overwrite(self):
        result = self.build()
        before = (result["folder"]/"scaler.json").read_bytes()
        with self.assertRaises(FileExistsError): self.build()
        self.assertEqual(before,(result["folder"]/"scaler.json").read_bytes())

    def test_wrong_snapshot_and_tampered_state_rejected(self):
        result = self.build()
        with self.assertRaises(ValueError): self.load(result["folder"],version="other")
        with self.assertRaises(ValueError): self.load(result["folder"],hashes={})
        (result["folder"]/"scaler.json").write_text("{}",encoding="utf-8")
        with self.assertRaises(ValueError): self.load(result["folder"])

    def test_bad_fit_contract_or_environment_rejected(self):
        result = self.build()
        path = result["folder"]/"manifest.json"
        original = json.loads(path.read_text())
        for key,value in [("fit_split","test"),("fit_last_date","2024-01-02"),("fit_row_count",99)]:
            changed = json.loads(json.dumps(original))
            changed["metadata"][key] = value
            path.write_text(json.dumps(changed),encoding="utf-8")
            with self.subTest(key=key),self.assertRaises(ValueError): self.load(result["folder"])
        original["sklearn_version"] = "wrong"
        path.write_text(json.dumps(original),encoding="utf-8")
        with self.assertRaises(ValueError): self.load(result["folder"])

    def test_snapshot_rejection_prevents_fit_or_write(self):
        with patch("backend.data.preparation.train_scaler.load_tv1_snapshot",side_effect=ValueError("bad snapshot")), patch.object(StandardScaler,"fit",side_effect=AssertionError("must not fit")):
            with self.assertRaises(ValueError): build_train_scaler(self.root,"fixture")
        self.assertFalse((self.root/"artifacts").exists())


if __name__ == "__main__": unittest.main()
