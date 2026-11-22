"""Synthetic saved-batch regression tests; no real snapshot required."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from backend.artifacts.prepared import save_prepared_modes,load_prepared_modes
from backend.data.preparation.windows import create_one_step_windows,create_five_step_windows
from backend.data.preparation.contracts import validate_window_result


class PreparedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        dates = (pd.bdate_range("2022-10-03",periods=40).strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2023-12-01",periods=8).strftime("%Y-%m-%d").tolist()
                 + pd.bdate_range("2024-01-02",periods=8).strftime("%Y-%m-%d").tolist())
        self.data = pd.DataFrame({"date":dates,"ticker":"AAPL","adjusted_close":np.arange(1.,57.),"dataset_version":"fixture"})
        self.scaler = StandardScaler().fit(np.arange(1.,41.).reshape(-1,1))
        self.results = {1:create_one_step_windows(self.data,self.scaler),5:create_five_step_windows(self.data,self.scaler)}
        self.hashes = {"validated":"a"*64}
        self.folder = save_prepared_modes(self.results,self.root,"prepared","scaler",self.hashes)

    def load(self,**kwargs):
        return load_prepared_modes(self.folder,expected_dataset_version=kwargs.get("version","fixture"),
                                   expected_source_hashes=kwargs.get("hashes",self.hashes),expected_scaler_id=kwargs.get("scaler_id","scaler"))

    def test_roundtrip_both_modes_exact_and_separate_targets(self):
        loaded,_ = self.load()
        for h,result in loaded.items():
            self.assertTrue(validate_window_result(result,self.data,self.scaler)["passed"])
            for split,batch in result["splits"].items():
                for key in ["X","y","target_indices"]: np.testing.assert_array_equal(batch[key],self.results[h]["splits"][split][key])
                self.assertNotIn("target_values",batch["inputs"][0])
        self.assertTrue((self.folder/"f5_train_inputs.json").is_file())
        self.assertTrue((self.folder/"f5_train_targets.json").is_file())

    def test_corrupt_payload_rejected(self):
        (self.folder/"f1_train.npz").write_bytes(b"corrupt")
        with self.assertRaises(ValueError): self.load()

    def test_wrong_dataset_hash_scaler_rejected(self):
        for values in [{"version":"wrong"},{"hashes":{}},{"scaler_id":"wrong"}]:
            with self.subTest(values=values),self.assertRaises(ValueError): self.load(**values)

    def test_manifest_member_injection_rejected(self):
        path = self.folder/"manifest.json"
        manifest = json.loads(path.read_text())
        manifest["files"]["../outside.npz"] = "0"*64
        path.write_text(json.dumps(manifest),encoding="utf-8")
        with self.assertRaises(ValueError): self.load()

    def test_existing_id_or_unsafe_id_not_overwritten(self):
        before = (self.folder/"manifest.json").read_bytes()
        with self.assertRaises(FileExistsError): save_prepared_modes(self.results,self.root,"prepared","scaler",self.hashes)
        self.assertEqual(before,(self.folder/"manifest.json").read_bytes())
        with self.assertRaises(ValueError): save_prepared_modes(self.results,self.root,"../outside","scaler",self.hashes)


if __name__ == "__main__": unittest.main()
