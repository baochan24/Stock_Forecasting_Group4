"""Fit/save/reload a train-only scaler and record acceptance checks."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from backend.data.preparation.train_scaler import build_train_scaler
from backend.artifacts.scaler import load_scaler
from backend.data.transforms.scaling import scale, inverse_scale


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version",required=True)
    args = parser.parse_args()
    result = build_train_scaler(ROOT,args.dataset_version)
    fitted = result["scaler"]
    snapshot = result["snapshot"]
    loaded, manifest = load_scaler(result["folder"],expected_dataset_version=args.dataset_version,
                                   expected_source_hashes=snapshot["acceptance"]["hashes"])
    all_prices = result["plan"]["data"].adjusted_close.to_numpy().reshape(-1,1)
    saved_mean, saved_var = loaded.mean_.copy(), loaded.var_.copy()
    np.testing.assert_allclose(scale(all_prices,loaded),scale(all_prices,fitted),rtol=0,atol=0)
    restored = inverse_scale(scale(all_prices,loaded),loaded)
    np.testing.assert_allclose(restored,all_prices,rtol=1e-12,atol=1e-12)
    np.testing.assert_array_equal(saved_mean,loaded.mean_)
    np.testing.assert_array_equal(saved_var,loaded.var_)
    summary = {"passed":True,"dataset_version":args.dataset_version,"scaler_folder":str(result["folder"]),
               "manifest":manifest,"mean":loaded.mean_.tolist(),"variance":loaded.var_.tolist(),
               "scale":loaded.scale_.tolist(),"n_samples_seen":int(loaded.n_samples_seen_),
               "roundtrip_max_abs_error":float(np.max(np.abs(restored-all_prices))),
               "reload_transform_exact":True,"transform_did_not_refit":True,
               "environment":{"python":sys.version,"executable":sys.executable,"sklearn":sklearn.__version__},
               "scope":"Train scaler only; transforms inspect equivalence, no model tuning/evaluation."}
    folder = ROOT/"logs/audit"/("tv2_scaler_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    with (folder/"summary.json").open("x",encoding="utf-8") as stream:
        json.dump(summary,stream,indent=2,allow_nan=False)
    print(json.dumps({k:summary[k] for k in ["passed","scaler_folder","mean","variance","scale","n_samples_seen","roundtrip_max_abs_error"]},indent=2))
    print(f"Evidence: {folder/'summary.json'}")


if __name__ == "__main__": main()
