"""Audit both modes against TV1 and verify input-only preparation adapter."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.windows import create_one_step_windows,create_five_step_windows
from backend.data.preparation.contracts import validate_window_result,build_inference_inputs
from backend.artifacts.scaler import load_scaler
from backend.data.validation.validator import compute_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version",required=True)
    parser.add_argument("--scaler-dir",required=True)
    args = parser.parse_args()
    snapshot = load_tv1_snapshot(ROOT,args.dataset_version)
    files = [Path(p) for p in snapshot["paths"].values()]+[Path(args.scaler_dir)/"manifest.json",Path(args.scaler_dir)/"scaler.json"]
    before = {str(p):compute_sha256(p) for p in files}
    checks, ids = [],set()
    with patch.object(StandardScaler,"fit",side_effect=AssertionError("no fit")),patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("no fit")):
        scaler,manifest = load_scaler(args.scaler_dir,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot["acceptance"]["hashes"])
        for create in [create_one_step_windows,create_five_step_windows]:
            result = create(snapshot["data"],scaler)
            check = validate_window_result(result,snapshot["data"],scaler)
            for batch in result["splits"].values():
                packed = build_inference_inputs(batch["inputs"],scaler)
                np.testing.assert_array_equal(packed["X"],batch["X"])
                for record in packed["inputs"]:
                    if record["sample_id"] in ids: raise AssertionError("Cross-mode duplicate ID")
                    ids.add(record["sample_id"])
            check["input_only_adapter_matches_X"] = True
            checks.append(check)
    if before != {str(p):compute_sha256(p) for p in files}: raise AssertionError("Artifacts changed")
    summary = {"passed":True,"dataset_version":args.dataset_version,"scaler_id":manifest["scaler_id"],
               "checks":checks,"unique_ids_both_modes":len(ids),"artifact_hashes":before,
               "fit_and_partial_fit_forbidden":True,"python":sys.version,"executable":sys.executable,
               "scope":"TV2 contract and input-only preparation adapter, not model/API inference or full leakage certification."}
    folder = ROOT/"logs/audit"/("tv2_contracts_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    with (folder/"summary.json").open("x",encoding="utf-8") as stream: json.dump(summary,stream,indent=2)
    print(json.dumps({"passed":True,"checks":checks,"unique_ids":len(ids),"evidence":str(folder/"summary.json")},indent=2))


if __name__ == "__main__": main()
