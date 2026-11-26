"""Validate TV2 Forecast Input/Target contracts without implementing inference."""
from copy import deepcopy
from datetime import date
import re

import numpy as np

from backend.data.preparation.preparation import create_split_plan, target_split
from backend.data.transforms.scaling import scale

INPUT_FIELDS = {"sample_id","dataset_version","forecast_origin","input_dates","input_values","lookback","forecast_length"}
TARGET_FIELDS = {"sample_id","target_dates","target_values","split","horizon_step"}


def _dates(values, count):
    if not isinstance(values,list) or len(values) != count:
        raise ValueError("Wrong date count/type")
    for value in values:
        if not isinstance(value,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",value):
            raise ValueError("Expected YYYY-MM-DD dates")
        date.fromisoformat(value)
    if values != sorted(set(values)):
        raise ValueError("Dates must be unique and increasing")


def _prices(values, shape):
    array = np.asarray(values)
    if array.shape != shape or array.dtype.kind not in "iuf" or not np.isfinite(array).all() or (array <= 0).any():
        raise ValueError("Raw prices must be positive finite numbers of exact shape")
    return array


def validate_forecast_input(record):
    """Reject target fields/extra fields; validate one raw input, not its source.

    Session continuity/source authentication require the accepted snapshot in
    validate_window_result. Does not read targets, fit or cast model tensors.
    """
    if not isinstance(record,dict) or set(record) != INPUT_FIELDS:
        raise ValueError("Forecast Input must contain only the seven input fields")
    if type(record["lookback"]) is not int or record["lookback"] not in (10,30,60):
        raise ValueError("lookback must be 10, 30 or 60")
    h = record["forecast_length"]
    if type(h) is not int or h not in (1,5): raise ValueError("forecast_length must be 1 or 5")
    version = record["dataset_version"]
    if not isinstance(version,str) or not re.fullmatch(r"[A-Za-z0-9_-]+",version):
        raise ValueError("Invalid dataset_version")
    _dates(record["input_dates"],record["lookback"])
    if record["forecast_origin"] != record["input_dates"][-1]: raise ValueError("Origin must equal last input session")
    if not all("2015-01-01" <= d <= "2025-12-31" for d in record["input_dates"]):
        raise ValueError("Input dates outside project scope")
    _prices(record["input_values"],(record["lookback"],1))
    expected_id = f"{version}:lb{record['lookback']}:f{h}:{record['forecast_origin']}"
    if record["sample_id"] != expected_id: raise ValueError("ID/version/mode/origin mismatch")


def build_inference_inputs(inputs, scaler):
    """Return independent {inputs, X} from input records only; never accept targets.

    This is a preparation adapter, not a model/API inference implementation.
    Homogeneous non-empty batch, same dataset_version and forecast_length.
    """
    if not isinstance(inputs,list) or not inputs: raise ValueError("Expected a non-empty input record list")
    for record in inputs: validate_forecast_input(record)
    if len({(x["dataset_version"],x["forecast_length"],x["lookback"]) for x in inputs}) != 1:
        raise ValueError("Mixed dataset versions or forecast modes")
    if len({x["sample_id"] for x in inputs}) != len(inputs): raise ValueError("Duplicate sample_id")
    return {"inputs":deepcopy(inputs),"X":scale(np.stack([x["input_values"] for x in inputs]),scaler)}


def validate_window_result(result, validated_data, scaler):
    """Check record/batch/date/price/scaling alignment against full accepted data.

    Raises ValueError on contract failure. Call after snapshot/scaler acceptance;
    does not certify all possible leakage paths or consumer model behavior.
    """
    plan = create_split_plan(validated_data)
    data = plan["data"]
    h = result.get("forecast_length")
    lookback = result.get("lookback")
    if type(h) is not int or h not in (1,5) or type(lookback) is not int or lookback not in (10,30,60) or result.get("dataset_version") != plan["dataset_version"]:
        raise ValueError("Window result identity mismatch")
    if set(result["splits"]) != {"train","val","test"}: raise ValueError("Wrong split keys")
    seen = set()
    for split,batch in result["splits"].items():
        count = batch["num_samples"]
        if type(count) is not int or count < 0: raise ValueError("Invalid count")
        if len(batch["inputs"]) != count or len(batch["targets"]) != count: raise ValueError("Record count mismatch")
        X,y = np.asarray(batch["X"]),np.asarray(batch["y"])
        if X.shape != (count,lookback,1) or y.shape != (count,h) or X.dtype != np.float64 or y.dtype != np.float64:
            raise ValueError("Wrong batch shape/dtype")
        if not np.isfinite(X).all() or not np.isfinite(y).all(): raise ValueError("Nonfinite batch")
        indices = np.asarray(batch["target_indices"])
        if indices.shape != (count,) or indices.dtype.kind not in "iu" or (np.diff(indices) <= 0).any():
            raise ValueError("Invalid target indices")
        for n,(inp,target) in enumerate(zip(batch["inputs"],batch["targets"])):
            validate_forecast_input(inp)
            if inp["lookback"] != lookback or inp["dataset_version"] != plan["dataset_version"] or inp["forecast_length"] != h: raise ValueError("Record identity mismatch")
            if inp["sample_id"] in seen: raise ValueError("Duplicate sample_id")
            seen.add(inp["sample_id"])
            if not isinstance(target,dict) or set(target) != TARGET_FIELDS: raise ValueError("Wrong target fields")
            if target["sample_id"] != inp["sample_id"]: raise ValueError("Input/target ID mismatch")
            _dates(target["target_dates"],h)
            _prices(target["target_values"],(h,))
            if target["split"] != split or target_split(target["target_dates"]) != split: raise ValueError("Target split mismatch")
            if target["horizon_step"] != list(range(1,h+1)): raise ValueError("Horizon mismatch")
            i = int(indices[n])
            if i < lookback or i+h > len(data): raise ValueError("Index outside eligible history")
            if inp["input_dates"] != data.date.iloc[i-lookback:i].tolist() or target["target_dates"] != data.date.iloc[i:i+h].tolist():
                raise ValueError("Dates are not consecutive snapshot sessions")
            raw_x = data.adjusted_close.iloc[i-lookback:i].to_numpy().reshape(lookback,1)
            raw_y = data.adjusted_close.iloc[i:i+h].to_numpy()
            if not np.array_equal(inp["input_values"],raw_x) or not np.array_equal(target["target_values"],raw_y):
                raise ValueError("Raw price alignment mismatch")
            if not np.allclose(X[n],scale(raw_x,scaler),rtol=1e-12,atol=1e-12) or not np.allclose(y[n],scale(raw_y,scaler),rtol=1e-12,atol=1e-12):
                raise ValueError("Scaled price alignment mismatch")
    return {"passed":True,"forecast_length":h,"sample_count":len(seen),"split_counts":{k:b["num_samples"] for k,b in result["splits"].items()}}
