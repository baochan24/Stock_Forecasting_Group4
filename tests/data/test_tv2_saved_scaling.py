"""Saved-scaler shape/numeric contract; arrays are synthetic, not windows."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from sklearn.preprocessing import StandardScaler

from backend.artifacts.scaler import save_scaler, load_scaler
from backend.data.transforms.scaling import scale, inverse_scale


class SavedScalingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.hashes = {k:"a"*64 for k in ["raw","metadata","validated","validation_report","quality_audit"]}
        meta = {"dataset_version":"fixture","source_hashes":self.hashes,"fit_split":"train",
                "feature":"adjusted_close","currency":"USD","fit_first_date":"2015-01-02",
                "fit_last_date":"2022-12-30","fit_row_count":3}
        fitted = StandardScaler().fit([[10.],[20.],[30.]])
        folder = save_scaler(fitted,meta,Path(self.temp.name),"fixture")
        self.scaler, _ = load_scaler(folder,expected_dataset_version="fixture",expected_source_hashes=self.hashes)

    def test_saved_scaler_formula_and_shapes(self):
        with patch.object(StandardScaler,"fit",side_effect=AssertionError("refit forbidden")), patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("partial fit forbidden")):
            for shape in [(1,30,1),(2,30,1),(1,1),(2,1),(1,5),(2,5)]:
                with self.subTest(shape=shape):
                    values = np.linspace(1.,300.,num=np.prod(shape)).reshape(shape)
                    result = scale(values,self.scaler)
                    np.testing.assert_allclose(result,(values-20.)/np.sqrt(200./3.),rtol=1e-12,atol=1e-12)
                    restored = inverse_scale(result,self.scaler)
                    np.testing.assert_allclose(restored,values,rtol=1e-12,atol=1e-12)
                    self.assertEqual(result.shape,shape)
                    self.assertEqual(restored.shape,shape)

    def test_noncontiguous_readonly_input_and_scaler_unchanged(self):
        source = np.arange(120,dtype=np.float64).reshape(2,60,1)+1
        values = source[:,::2,:]
        values.flags.writeable = False
        before = source.copy()
        state = {key:np.array(getattr(self.scaler,key),copy=True) for key in ["mean_","var_","scale_","n_samples_seen_"]}
        result = scale(values,self.scaler)
        result_before = result.copy()
        inverse_scale(result,self.scaler)
        np.testing.assert_array_equal(source,before)
        np.testing.assert_array_equal(result,result_before)
        self.assertFalse(np.shares_memory(values,result))
        for key,value in state.items(): np.testing.assert_array_equal(getattr(self.scaler,key),value)

    def test_negative_zero_scaled_values_are_not_clipped(self):
        z = np.array([[-2.,-1.,0.,1.,2.]])
        restored = inverse_scale(z,self.scaler)
        np.testing.assert_allclose(restored,20.+z*np.sqrt(200./3.),rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(scale(restored,self.scaler),z,rtol=1e-12,atol=1e-12)

    def test_integer_float32_values_become_float64(self):
        for dtype in [np.int64,np.float32,np.float64]:
            values = np.array([[10,20,30,40,50]],dtype=dtype)
            result = scale(values,self.scaler)
            self.assertEqual(result.dtype,np.float64)
            np.testing.assert_allclose(inverse_scale(result,self.scaler),values,rtol=1e-12,atol=1e-12)

    def test_constant_train_scaler_roundtrip(self):
        constant = StandardScaler().fit([[20.],[20.],[20.]])
        meta = {"dataset_version":"fixture","source_hashes":self.hashes,"fit_split":"train",
                "feature":"adjusted_close","currency":"USD","fit_first_date":"2015-01-02",
                "fit_last_date":"2022-12-30","fit_row_count":3}
        folder = save_scaler(constant,meta,Path(self.temp.name),"constant")
        loaded, _ = load_scaler(folder,expected_dataset_version="fixture",expected_source_hashes=self.hashes)
        np.testing.assert_array_equal(loaded.scale_,[1.])
        values = np.array([[10.,20.,30.,40.,50.]])
        np.testing.assert_array_equal(inverse_scale(scale(values,loaded),loaded),values)


if __name__ == "__main__": unittest.main()
