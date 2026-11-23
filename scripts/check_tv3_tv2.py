"""Verify official TV2 artifacts → lossless float64 adapter → TV3 CPU forward."""
import argparse
from datetime import datetime,timezone
import importlib.metadata as metadata
import json
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.tensors import make_lstm_inputs,make_lstm_training_batch
from backend.artifacts.prepared import load_prepared_modes
from backend.artifacts.scaler import load_scaler
from backend.audit.tv2_leakage import audit_temporal_windows,audit_train_statistics
from backend.data.transforms.scaling import inverse_scale
from backend.data.validation.validator import compute_sha256
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version",required=True)
    parser.add_argument("--scaler-dir",required=True)
    parser.add_argument("--prepared-dir",required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    snapshot = load_tv1_snapshot(ROOT,args.dataset_version)
    paths = [Path(p) for p in snapshot["paths"].values()]
    paths += [Path(args.scaler_dir)/n for n in ["manifest.json","scaler.json"]]
    paths += [p for p in Path(args.prepared_dir).iterdir() if p.is_file()]
    hashes = {str(p):compute_sha256(p) for p in paths}
    checks = []
    with patch.object(StandardScaler,"fit",side_effect=AssertionError("fit forbidden")),patch.object(StandardScaler,"partial_fit",side_effect=AssertionError("partial_fit forbidden")):
        scaler,scaler_manifest = load_scaler(args.scaler_dir,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot["acceptance"]["hashes"])
        results,prepared_manifest = load_prepared_modes(args.prepared_dir,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot["acceptance"]["hashes"],expected_scaler_id=scaler_manifest["scaler_id"])
        audit_train_statistics(snapshot["data"],scaler,scaler_manifest["metadata"])
        scaler_before = {k:np.array(getattr(scaler,k),copy=True) for k in ["mean_","var_","scale_","n_samples_seen_"]}
        for h,cls in [(1,LSTMOneStep),(5,LSTMMultiStep)]:
            audit_temporal_windows(results[h],snapshot["data"],scaler)
            torch.manual_seed(42)  # Unit integration seed, no model/seed selection.
            model = cls().cpu().eval()
            before = {k:v.clone() for k,v in model.state_dict().items()}
            for split,batch in results[h]["splits"].items():
                packed = make_lstm_training_batch(batch,scaler,dataset_version=args.dataset_version,forecast_length=h)
                input_only = make_lstm_inputs(batch["inputs"],scaler,dataset_version=args.dataset_version,forecast_length=h)
                torch.testing.assert_close(packed["X"],input_only["X"],rtol=0,atol=0)
                raw_targets = np.stack([r["target_values"] for r in batch["targets"]])
                restored = inverse_scale(packed["y"].numpy(),scaler)
                np.testing.assert_array_equal(packed["X"].numpy(),batch["X"])
                np.testing.assert_array_equal(packed["y"].numpy(),batch["y"])
                if packed["X"].dtype != torch.float64 or any(p.dtype != torch.float64 for p in model.parameters()):
                    raise AssertionError("Expected float64 model and tensors")
                np.testing.assert_allclose(restored,raw_targets,rtol=1e-12,atol=1e-12)
                with torch.no_grad():
                    for start in range(0,len(packed["X"]),128):
                        x = input_only["X"][start:start+128]
                        prediction = model(x)  # Model receives X only, never y or records.
                        if prediction.shape != (len(x),h) or not torch.isfinite(prediction).all(): raise AssertionError("Forward output mismatch")
                        if not np.isfinite(inverse_scale(prediction.numpy(),scaler)).all(): raise AssertionError("Nonfinite inverse")
                checks.append({"forecast_length":h,"split":split,"samples":batch["num_samples"],
                               "X_shape":list(packed["X"].shape),"y_shape":list(packed["y"].shape),
                               "tensor_X_max_abs_difference_scaled":float(np.max(np.abs(packed["X"].numpy()-batch["X"]))),
                               "target_roundtrip_max_abs_error_usd":float(np.max(np.abs(restored-raw_targets))),
                               "input_only_matches_training_X":True,"cpu_float64_forward_finite":True,
                               "sample_ids_and_order_preserved":packed["sample_ids"] == [r["sample_id"] for r in batch["inputs"]]})
            for k,v in model.state_dict().items():
                if not torch.equal(v,before[k]): raise AssertionError("Model state changed")
            if any(p.grad is not None for p in model.parameters()): raise AssertionError("Unexpected gradients")
        for k,v in scaler_before.items(): np.testing.assert_array_equal(getattr(scaler,k),v)
    if hashes != {str(p):compute_sha256(p) for p in paths}: raise AssertionError("Protected artifacts changed")
    source_paths = [ROOT/"backend/data/preparation/tensors.py",ROOT/"backend/models/lstm_one_step/model.py",ROOT/"backend/models/lstm_multi_step/model.py",Path(__file__)]
    summary = {"passed":True,"dataset_version":args.dataset_version,"scaler_id":scaler_manifest["scaler_id"],"prepared_id":prepared_manifest["prepared_id"],
               "checks":checks,"total_forward_samples":sum(c["samples"] for c in checks),"artifact_hashes":hashes,
               "source_hashes":{p.relative_to(ROOT).as_posix():compute_sha256(p) for p in source_paths},
               "packages":{n:metadata.version(n) for n in ["torch","pytest","numpy","scikit-learn"]},
               "python":sys.version,"executable":sys.executable,"model_weights":"untrained seed42 smoke-test only",
               "dtype":"float64","tolerances":{"tensor_copy_max_error":0,"target_usd_rtol":1e-12,"target_usd_atol":1e-12},
               "scope":"Input contract/dtype/forward integration only, no optimizer/loss/forecast metrics or model selection."}
    folder = ROOT/"logs/audit"/("tv3_tv2_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    (folder/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"passed":True,"total_forward_samples":summary["total_forward_samples"],"checks":checks,"evidence":str(folder/"summary.json")},indent=2))


if __name__ == "__main__": main()
