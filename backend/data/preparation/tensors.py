"""Lossless CPU float64 boundary from accepted TV2 records to model tensors."""
from copy import deepcopy
import numpy as np
import torch

from backend.data.preparation.contracts import build_inference_inputs, TARGET_FIELDS
from backend.data.preparation.preparation import target_split
from backend.data.transforms.scaling import scale


def _input_pack(inputs, scaler, dataset_version, forecast_length):
    if type(forecast_length) is not int or forecast_length not in (1,5):
        raise ValueError("Expected forecast_length 1 or 5")
    packed = build_inference_inputs(inputs,scaler)
    for record in packed["inputs"]:
        if record["dataset_version"] != dataset_version or record["forecast_length"] != forecast_length:
            raise ValueError("Input dataset/mode mismatch")
    return packed


def _float64(values):
    values = np.asarray(values)
    if values.dtype != np.float64: raise ValueError("Expected TV2 float64 array")
    result = torch.tensor(values,dtype=torch.float64,device="cpu")
    if not torch.isfinite(result).all(): raise ValueError("float64 conversion produced NaN/Inf")
    if not np.array_equal(result.numpy(),values): raise ValueError("float64 tensor copy changed values")
    return result


def make_lstm_inputs(inputs, scaler, *, dataset_version, forecast_length):
    """Accept only Forecast Input records, return CPU float64 X and identity.

    Caller must accept snapshot/scaler first. No target/y argument or fitting.
    Tensor copy preserves float64 values exactly, with no precision downcast.
    Data/scaler artifacts remain float64 and are never rewritten.
    """
    packed = _input_pack(inputs,scaler,dataset_version,forecast_length)
    return {"X":_float64(packed["X"]),"inputs":packed["inputs"],
            "sample_ids":[r["sample_id"] for r in packed["inputs"]],
            "dataset_version":dataset_version,"forecast_length":forecast_length}


def make_lstm_training_batch(batch, scaler, *, dataset_version, forecast_length):
    """Convert a verified TV2 batch for loss computation, preserving record order.

    Checks arrays against records/scaler and input/target pairing. Snapshot
    session continuity/full coverage must be verified before this low-level call.
    This performs neither optimizer steps nor loss/metric evaluation.
    """
    packed = _input_pack(batch["inputs"],scaler,dataset_version,forecast_length)
    count = len(packed["inputs"])
    if batch["num_samples"] != count or len(batch["targets"]) != count:
        raise ValueError("Batch count mismatch")
    X,y = np.asarray(batch["X"]),np.asarray(batch["y"])
    if X.shape != (count,packed["inputs"][0]["lookback"],1) or y.shape != (count,forecast_length):
        raise ValueError("Wrong batch tensor shape")
    if X.dtype != np.float64 or y.dtype != np.float64 or not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("TV2 arrays must be finite float64")
    if not np.allclose(X,packed["X"],rtol=1e-12,atol=1e-12): raise ValueError("X does not match input records")
    values = []
    splits = set()
    for inp,target in zip(packed["inputs"],batch["targets"]):
        if not isinstance(target,dict) or set(target) != TARGET_FIELDS: raise ValueError("Wrong target schema")
        if target["sample_id"] != inp["sample_id"]: raise ValueError("Input/target pairing mismatch")
        dates = target["target_dates"]
        if len(dates) != forecast_length or target_split(dates) != target["split"] or dates[0] <= inp["forecast_origin"]:
            raise ValueError("Target dates/split mismatch")
        if target["horizon_step"] != list(range(1,forecast_length+1)): raise ValueError("Wrong target horizon")
        raw = np.asarray(target["target_values"])
        if raw.shape != (forecast_length,) or raw.dtype.kind not in "iuf" or not np.isfinite(raw).all() or (raw <= 0).any():
            raise ValueError("Invalid raw target values")
        values.append(raw)
        splits.add(target["split"])
    if len(splits) != 1: raise ValueError("Mixed target splits")
    expected_y = scale(np.stack(values),scaler)
    if not np.allclose(y,expected_y,rtol=1e-12,atol=1e-12): raise ValueError("y does not match target records")
    return {"X":_float64(X),"y":_float64(y),"inputs":packed["inputs"],"targets":deepcopy(batch["targets"]),
            "sample_ids":[r["sample_id"] for r in packed["inputs"]],"dataset_version":dataset_version,
            "forecast_length":forecast_length,"split":next(iter(splits))}
