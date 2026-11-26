"""Dated 1/5-step windows from accepted history, split by all target dates."""
import numpy as np

from backend.data.preparation.preparation import create_split_plan
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.transforms.scaling import scale
from backend.artifacts.scaler import load_scaler


def _create_windows(validated_data, scaler, forecast_length, lookback=30):
    """Return split batches with separate inputs/targets, raw and scaled arrays.

    Low-level helper: caller must accept the snapshot and linked scaler first.
    Lookback supports 10/30/60, default 30; never fit or alter the scaler.
    All numeric arrays are float64; model tensor conversion is not performed.
    Empty eligible splits retain (0,lookback,1)/(0,forecast_length) shapes.
    Exclusion counts are disjoint: history first, then missing future targets,
    then targets crossing split. Never delete any rows from source history.
    """
    if type(lookback) is not int or lookback not in (10, 30, 60):
        raise ValueError("Unsupported lookback")
    plan = create_split_plan(validated_data)
    data = plan["data"]
    dates = data.date.tolist()
    prices = data.adjusted_close.to_numpy(dtype=np.float64).reshape(-1,1)
    scaled = scale(prices,scaler)
    version = plan["dataset_version"]
    result = {}
    for split, indices in plan["target_indices"].items():
        candidates = indices[indices >= lookback]
        eligible = []
        crossing, incomplete = 0, 0
        for position in candidates:
            i = int(position)
            if i + forecast_length > len(data):
                incomplete += 1
            elif i + forecast_length - 1 > int(indices[-1]):
                crossing += 1
            else:
                eligible.append(i)
        eligible = np.asarray(eligible,dtype=np.int64)
        inputs, targets = [], []
        for position in eligible:
            i = int(position)
            sample_id = f"{version}:lb{lookback}:f{forecast_length}:{dates[i-1]}"
            inputs.append({"sample_id":sample_id,"dataset_version":version,
                           "forecast_origin":dates[i-1],"input_dates":dates[i-lookback:i],
                           "input_values":prices[i-lookback:i].copy(),"lookback":lookback,"forecast_length":forecast_length})
            targets.append({"sample_id":sample_id,"target_dates":dates[i:i+forecast_length],
                            "target_values":prices[i:i+forecast_length,0].copy(),"split":split,
                            "horizon_step":list(range(1,forecast_length+1))})
        X = np.stack([scaled[int(i)-lookback:int(i)] for i in eligible]) if len(eligible) else np.empty((0,lookback,1))
        y = (np.stack([scaled[int(i):int(i)+forecast_length,0] for i in eligible])
             if len(eligible) else np.empty((0,forecast_length)))
        result[split] = {"inputs":inputs,"targets":targets,"X":X,"y":y,
                         "target_indices":eligible.copy(),"num_samples":len(eligible),
                         "excluded_insufficient_history":int((indices < lookback).sum()),
                         "excluded_cross_split_targets":crossing,"excluded_incomplete_targets":incomplete}
    return {"dataset_version":version,"lookback":lookback,"forecast_length":forecast_length,"splits":result}


def create_one_step_windows(validated_data, scaler):
    """One-step batches; accepted full history required, no fit/refit."""
    return _create_windows(validated_data,scaler,1)


def create_five_step_windows(validated_data, scaler):
    """Direct 5-output batches, all 5 consecutive snapshot targets in one split.

    No recursive prediction and no future target fed into the current input.
    Empty X/y shapes are (0,lookback,1)/(0,5). No fitting or file writes.
    """
    return _create_windows(validated_data,scaler,5)


def prepare_one_step_windows(project_root, dataset_version, scaler_folder):
    """Accept TV1 artifacts and matching saved scaler, then create windows."""
    return _prepare_windows(project_root,dataset_version,scaler_folder,1)


def prepare_five_step_windows(project_root, dataset_version, scaler_folder):
    """Accept TV1 and its existing train scaler before direct 5-step windows."""
    return _prepare_windows(project_root,dataset_version,scaler_folder,5)


def _prepare_windows(project_root, dataset_version, scaler_folder, forecast_length):
    snapshot = load_tv1_snapshot(project_root,dataset_version)
    scaler, manifest = load_scaler(scaler_folder,expected_dataset_version=dataset_version,
                                   expected_source_hashes=snapshot["acceptance"]["hashes"])
    result = _create_windows(snapshot["data"],scaler,forecast_length)
    result["scaler_id"] = manifest["scaler_id"]
    result["source_hashes"] = snapshot["acceptance"]["hashes"]
    return result
