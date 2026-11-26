"""Audit all 1/5-step dated windows against the accepted snapshot, without training."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from backend.data.preparation.windows import prepare_one_step_windows, prepare_five_step_windows
from backend.artifacts.scaler import load_scaler
from backend.data.transforms.scaling import inverse_scale
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.validation.validator import compute_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version",required=True)
    parser.add_argument("--scaler-dir",required=True)
    parser.add_argument("--forecast-length",type=int,choices=[1,5],default=1)
    args = parser.parse_args()
    h = args.forecast_length
    snapshot = load_tv1_snapshot(ROOT,args.dataset_version)
    data = snapshot["data"]
    protected = [Path(p) for p in snapshot["paths"].values()] + [Path(args.scaler_dir)/"scaler.json",Path(args.scaler_dir)/"manifest.json"]
    before = {str(p):compute_sha256(p) for p in protected}
    with patch.object(StandardScaler,"fit",side_effect=AssertionError("fit forbidden")), patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("partial_fit forbidden")):
        prepare = prepare_one_step_windows if h == 1 else prepare_five_step_windows
        result = prepare(ROOT,args.dataset_version,args.scaler_dir)
        scaler,_ = load_scaler(args.scaler_dir,expected_dataset_version=args.dataset_version,
                              expected_source_hashes=snapshot["acceptance"]["hashes"])
    summaries = {}
    all_ids = []
    for split,batch in result["splits"].items():
        years = data.date.str[:4].astype(int)
        mask = years.between(2015,2022) if split == "train" else (years == 2023 if split == "val" else years.between(2024,2025))
        expected = [i for i in np.flatnonzero(mask.to_numpy()) if i >= 30 and i+h <= len(data) and mask.iloc[i:i+h].all()]
        if batch["target_indices"].tolist() != expected: raise AssertionError("Missing/extra target indices")
        if batch["X"].shape != (len(expected),30,1) or batch["y"].shape != (len(expected),h): raise AssertionError("Wrong shape")
        for n,(i,inp,target) in enumerate(zip(expected,batch["inputs"],batch["targets"])):
            if inp["input_dates"] != data.date.iloc[i-30:i].tolist(): raise AssertionError("Input dates mismatch")
            if target["target_dates"] != data.date.iloc[i:i+h].tolist(): raise AssertionError("Target mismatch")
            if target["horizon_step"] != list(range(1,h+1)): raise AssertionError("Horizon mismatch")
            if inp["forecast_origin"] != data.date.iloc[i-1] or inp["forecast_origin"] >= target["target_dates"][0]: raise AssertionError("Origin mismatch")
            np.testing.assert_array_equal(inp["input_values"].ravel(),data.adjusted_close.iloc[i-30:i].to_numpy())
            np.testing.assert_array_equal(target["target_values"],data.adjusted_close.iloc[i:i+h].to_numpy())
            np.testing.assert_allclose(inverse_scale(batch["X"][n],scaler),inp["input_values"],rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(inverse_scale(batch["y"][n],scaler),target["target_values"],rtol=1e-12,atol=1e-12)
            if inp["sample_id"] != target["sample_id"]: raise AssertionError("ID mismatch")
            all_ids.append(inp["sample_id"])
        first,last = batch["inputs"][0],batch["inputs"][-1]
        summaries[split] = {"num_samples":batch["num_samples"],"X_shape":list(batch["X"].shape),"y_shape":list(batch["y"].shape),
                            "excluded_insufficient_history":batch["excluded_insufficient_history"],
                            "excluded_cross_split_targets":batch["excluded_cross_split_targets"],
                            "excluded_incomplete_targets":batch["excluded_incomplete_targets"],
                            "first":{"input_start":first["input_dates"][0],"origin":first["forecast_origin"],"target":batch["targets"][0]["target_dates"][0]},
                            "last":{"origin":last["forecast_origin"],"targets":batch["targets"][-1]["target_dates"]}}
    if len(all_ids) != len(set(all_ids)): raise AssertionError("Duplicate sample IDs")
    if before != {str(p):compute_sha256(p) for p in protected}: raise AssertionError("Artifacts changed")
    summary = {"passed":True,"dataset_version":args.dataset_version,"scaler_id":result["scaler_id"],"splits":summaries,
               "source_and_scaler_hashes":before,"fit_forbidden":True,"checked_all_raw_windows":True,
               "forecast_length":h,"scope":"Dated windows only; no model training, metrics or release serialization."}
    prefix = "tv2_one_step_" if h == 1 else "tv2_five_step_"
    output = ROOT/"logs/audit"/(prefix+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    output.mkdir(parents=True,exist_ok=False)
    with (output/"summary.json").open("x",encoding="utf-8") as stream: json.dump(summary,stream,indent=2)
    print(json.dumps({"passed":True,"splits":summaries,"evidence":str(output/"summary.json")},indent=2))


if __name__ == "__main__": main()
