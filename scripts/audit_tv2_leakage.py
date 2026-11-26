"""Audit TV2 temporal coverage, train-only scaler and future-price perturbations."""
from datetime import datetime,timezone
from pathlib import Path
import argparse
import json
import sys
from unittest.mock import patch
import numpy as np
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv2_leakage import audit_temporal_windows,audit_train_statistics
from backend.artifacts.scaler import load_scaler
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.windows import create_one_step_windows,create_five_step_windows
from backend.data.preparation.contracts import build_inference_inputs
from backend.data.validation.validator import compute_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version",required=True)
    parser.add_argument("--scaler-dir",required=True)
    args = parser.parse_args()
    snapshot = load_tv1_snapshot(ROOT,args.dataset_version)
    data = snapshot["data"]
    paths = [Path(p) for p in snapshot["paths"].values()] + [Path(args.scaler_dir)/"scaler.json",Path(args.scaler_dir)/"manifest.json"]
    hashes = {str(p):compute_sha256(p) for p in paths}
    modes = []
    with patch.object(StandardScaler,"fit",side_effect=AssertionError("fit forbidden")),patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("partial_fit forbidden")):
        scaler,manifest = load_scaler(args.scaler_dir,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot["acceptance"]["hashes"])
        stats = audit_train_statistics(data,scaler,manifest["metadata"])
        state = {key:np.array(getattr(scaler,key),copy=True) for key in ["mean_","var_","scale_","n_samples_seen_"]}
        for create in [create_one_step_windows,create_five_step_windows]:
            original = create(data,scaler)
            check = audit_temporal_windows(original,data,scaler)
            perturbations = []
            for cut in ["2023-01-01","2024-01-01"]:
                # Synthetic in-memory perturbation only; never publish as accepted snapshot.
                changed = data.copy(deep=True)
                changed.loc[changed.date >= cut,"adjusted_close"] *= 10
                audit_train_statistics(changed,scaler,manifest["metadata"])
                altered = create(changed,scaler)
                compared = 0
                for split,batch in original["splits"].items():
                    other = altered["splits"][split]
                    np.testing.assert_array_equal(batch["target_indices"],other["target_indices"])
                    for n,inp in enumerate(batch["inputs"]):
                        if inp["forecast_origin"] < cut:
                            np.testing.assert_array_equal(batch["X"][n],other["X"][n])
                            compared += 1
                first_split = "val" if cut.startswith("2023") else "test"
                if np.array_equal(original["splits"][first_split]["y"][0],altered["splits"][first_split]["y"][0]):
                    raise AssertionError("Perturbation did not change future targets")
                perturbations.append({"cutoff":cut,"unchanged_past_inputs":compared,"future_target_changed":True})
            for batch in original["splits"].values():
                if batch["num_samples"]:
                    packed = build_inference_inputs(batch["inputs"],scaler)
                    np.testing.assert_array_equal(packed["X"],batch["X"])
            check["future_price_perturbations"] = perturbations
            check["input_only_adapter_matches"] = True
            modes.append(check)
        for key,value in state.items(): np.testing.assert_array_equal(getattr(scaler,key),value)
    if hashes != {str(p):compute_sha256(p) for p in paths}: raise AssertionError("Source artifacts changed")
    summary = {"passed":True,"dataset_version":args.dataset_version,"scaler_id":manifest["scaler_id"],
               "train_statistics":stats,"modes":modes,"artifact_hashes":hashes,"refit_forbidden":True,
               "python":sys.version,"executable":sys.executable,
               "limitations":["Local preprocessing audit only, not training/model or test-tuning behavior certification.",
                              "Yahoo adjusted prices are retrospective, not a perfect point-in-time backtest.",
                              "Calendar NASDAQ resolves XNYS as declared by TV1.",
                              "Perturbed copies are synthetic audit probes, not authenticated snapshots."]}
    folder = ROOT/"logs/audit"/("tv2_leakage_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    with (folder/"summary.json").open("x",encoding="utf-8") as stream: json.dump(summary,stream,indent=2)
    print(json.dumps({"passed":True,"fit_rows":stats["fit_rows"],"modes":[{k:m[k] for k in ["forecast_length","split_counts","future_price_perturbations"]} for m in modes],"evidence":str(folder/"summary.json")},indent=2))


if __name__ == "__main__": main()
