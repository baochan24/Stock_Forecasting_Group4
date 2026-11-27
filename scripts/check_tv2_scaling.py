"""Read-only saved-scaler checks on shape fixtures derived from accepted prices.

These reshaped fixtures are not dated forecasting windows or model samples.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
from sklearn.preprocessing import StandardScaler
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from backend.artifacts.scaler import load_scaler
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.preparation import create_split_plan
from backend.data.transforms.scaling import scale, inverse_scale
from backend.data.validation.validator import compute_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version",required=True)
    parser.add_argument("--scaler-dir",required=True)
    args = parser.parse_args()
    snapshot = load_tv1_snapshot(ROOT,args.dataset_version)
    folder = Path(args.scaler_dir).resolve()
    files = [folder/"scaler.json",folder/"manifest.json"]
    hashes_before = {str(p):compute_sha256(p) for p in files}
    results = []
    with patch.object(StandardScaler,"fit",side_effect=AssertionError("fit forbidden")), patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("partial_fit forbidden")):
        scaler, manifest = load_scaler(folder,expected_dataset_version=args.dataset_version,
                                       expected_source_hashes=snapshot["acceptance"]["hashes"])
        state = {key:np.array(getattr(scaler,key),copy=True) for key in ["mean_","var_","scale_","n_samples_seen_"]}
        plan = create_split_plan(snapshot["data"])
        for split,indices in plan["target_indices"].items():
            prices = plan["data"].iloc[indices].adjusted_close.to_numpy()
            fixtures = {"all_prices":prices.reshape(-1,1),"input_shape":prices[:60].reshape(2,30,1),
                        "target_one_shape":prices[:2].reshape(2,1),"target_five_shape":prices[:10].reshape(2,5)}
            for name,values in fixtures.items():
                before = values.copy()
                z = scale(values,scaler)
                z_before = z.copy()
                restored = inverse_scale(z,scaler)
                np.testing.assert_allclose(z,(values-scaler.mean_[0])/scaler.scale_[0],rtol=1e-12,atol=1e-12)
                np.testing.assert_allclose(restored,values,rtol=1e-12,atol=1e-12)
                np.testing.assert_array_equal(values,before)
                np.testing.assert_array_equal(z,z_before)
                if z.shape != values.shape or restored.shape != values.shape or z.dtype != np.float64:
                    raise AssertionError("Shape/dtype contract failed")
                results.append({"split":split,"fixture":name,"shape":list(values.shape),
                                "roundtrip_max_abs_error_usd":float(np.max(np.abs(restored-values)))})
        for key,value in state.items(): np.testing.assert_array_equal(getattr(scaler,key),value)
    hashes_after = {str(p):compute_sha256(p) for p in files}
    if hashes_before != hashes_after: raise AssertionError("Scaler files changed")
    for key,path in snapshot["paths"].items():
        if compute_sha256(Path(path)) != snapshot["acceptance"]["hashes"][key]:
            raise AssertionError("Snapshot changed")
    summary = {"passed":True,"dataset_version":args.dataset_version,"scaler_id":manifest["scaler_id"],
               "checks":results,"rtol":1e-12,"atol_usd":1e-12,"fit_and_partial_fit_forbidden":True,
               "input_and_state_unchanged":True,"artifact_hashes":hashes_after,
               "snapshot_hashes":snapshot["acceptance"]["hashes"],
               "environment":{"python":sys.version,"executable":sys.executable,"numpy":np.__version__,"sklearn":sklearn.__version__},
               "scope":"Shape/numeric fixtures only; no dated windows, new scaler, model training or test performance evaluation."}
    output = ROOT/"logs/audit"/("tv2_scaling_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    output.mkdir(parents=True,exist_ok=False)
    with (output/"summary.json").open("x",encoding="utf-8") as stream:
        json.dump(summary,stream,ensure_ascii=False,allow_nan=False,indent=2)
    print(json.dumps({"passed":True,"checks":len(results),"max_abs_error_usd":max(r["roundtrip_max_abs_error_usd"] for r in results),"evidence":str(output/"summary.json")},indent=2))


if __name__ == "__main__": main()
