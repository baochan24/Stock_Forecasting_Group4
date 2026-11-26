"""Verify an extracted TV2 handoff; no fit, model training or pickle loading."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from unittest.mock import patch
import importlib.metadata as metadata
import site
import numpy as np
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.prepared import load_prepared_modes
from backend.artifacts.scaler import load_scaler
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.windows import create_one_step_windows,create_five_step_windows
from backend.data.preparation.contracts import build_inference_inputs
from backend.audit.tv2_leakage import audit_train_statistics,audit_temporal_windows
from backend.data.validation.validator import compute_sha256


def main():
    handoff = json.loads((ROOT/"HANDOFF.json").read_text(encoding="utf-8"))
    for relative,digest in handoff["files"].items():
        path = (ROOT/relative).resolve()
        if not path.is_relative_to(ROOT) or compute_sha256(path) != digest:
            raise ValueError(f"Handoff checksum/path mismatch: {relative}")
    snapshot = load_tv1_snapshot(ROOT,handoff["dataset_version"])
    folder = ROOT/"artifacts/scalers"/handoff["scaler_id"]
    with patch.object(StandardScaler,"fit",side_effect=AssertionError("fit forbidden")),patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("partial_fit forbidden")):
        scaler,manifest = load_scaler(folder,expected_dataset_version=handoff["dataset_version"],expected_source_hashes=snapshot["acceptance"]["hashes"])
        results,_ = load_prepared_modes(ROOT/"data/prepared"/handoff["prepared_id"],expected_dataset_version=handoff["dataset_version"],
                                       expected_source_hashes=snapshot["acceptance"]["hashes"],expected_scaler_id=handoff["scaler_id"])
        train = audit_train_statistics(snapshot["data"],scaler,manifest["metadata"])
        checks = []
        for h,create in [(1,create_one_step_windows),(5,create_five_step_windows)]:
            saved = results[h]
            check = audit_temporal_windows(saved,snapshot["data"],scaler)
            rebuilt = create(snapshot["data"],scaler)
            for split,batch in saved["splits"].items():
                for key in ["X","y","target_indices"]:
                    np.testing.assert_array_equal(batch[key],rebuilt["splits"][split][key])
                np.testing.assert_array_equal(build_inference_inputs(batch["inputs"],scaler)["X"],batch["X"])
            checks.append({k:check[k] for k in ["passed","forecast_length","split_counts"]})
    for relative,digest in handoff["files"].items():
        if compute_sha256(ROOT/relative) != digest: raise ValueError("Protected handoff file changed")
    summary = {"passed":True,"dataset_version":handoff["dataset_version"],"checks":checks,"train_rows":train["fit_rows"],
               "reload_equals_rebuild_exactly":True,"refit_forbidden":True,
               "python":sys.version,"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,
               "user_site_enabled":site.ENABLE_USER_SITE,
               "packages":{n:metadata.version(n) for n in ["numpy","pandas","scikit-learn","exchange_calendars"]},
               "recipient_machine_verified":False,"scope":"Local verification; recipient records their own machine confirmation separately."}
    folder = ROOT/"logs/audit"/("tv2_handoff_verify_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    with (folder/"summary.json").open("x",encoding="utf-8") as stream: json.dump(summary,stream,indent=2)
    print(json.dumps({"passed":True,"checks":checks,"evidence":str(folder/"summary.json"),"user_site_enabled":site.ENABLE_USER_SITE},indent=2))


if __name__ == "__main__": main()
