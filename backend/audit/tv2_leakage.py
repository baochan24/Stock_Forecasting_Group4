"""Independent temporal coverage and train-statistics audit for TV2 outputs."""
import numpy as np

from backend.data.preparation.contracts import validate_window_result


def _split(date):
    if "2015-01-01" <= date <= "2022-12-31": return "train"
    if "2023-01-01" <= date <= "2023-12-31": return "val"
    if "2024-01-01" <= date <= "2025-12-31": return "test"
    raise ValueError("Date outside project range")


def audit_train_statistics(data, scaler, metadata):
    """Recompute numpy moments from all train rows, independently of fit helper.

    This verifies agreement, not a historical proof of who originally called fit.
    Current fit orchestration also has separate spy/metamorphic regression tests.
    """
    train = data.loc[(data.date >= "2015-01-01") & (data.date <= "2022-12-31")]
    values = train.adjusted_close.to_numpy(dtype=np.float64)
    if not len(values): raise ValueError("No train rows")
    mean, variance = float(np.mean(values)),float(np.var(values,ddof=0))
    expected_scale = float(np.sqrt(variance)) if variance else 1.
    for field, expected in [("mean_",mean),("var_",variance),("scale_",expected_scale)]:
        actual = np.asarray(getattr(scaler,field))
        if actual.shape != (1,) or not np.allclose(actual,[expected],rtol=1e-12,atol=1e-12):
            raise ValueError(f"Scaler does not match train-only {field}")
    if int(scaler.n_samples_seen_) != len(train): raise ValueError("Scaler fit count is not train row count")
    if (metadata.get("fit_first_date") != str(train.date.iloc[0]) or metadata.get("fit_last_date") != str(train.date.iloc[-1])
            or metadata.get("fit_row_count") != len(train) or metadata.get("fit_split") != "train"):
        raise ValueError("Scaler fit metadata is not exact full train range")
    return {"passed":True,"fit_rows":len(train),"mean":mean,"variance_ddof0":variance,"scale":expected_scale}


def audit_temporal_windows(result, data, scaler):
    """Enumerate eligible targets directly from source dates, without split plan.

    Full accepted source order is required; no sorting or gap-filling here.
    Detects missing/extra/reordered samples and wrong exclusion accounting.
    """
    dates = data.date.tolist()
    if dates != sorted(set(dates)): raise ValueError("Audit source must be unique and ordered")
    h = result["forecast_length"]
    if type(h) is not int or h not in (1,5): raise ValueError("Unsupported forecast length")
    expected = {s:[] for s in ["train","val","test"]}
    excluded = {s:{"history":0,"incomplete":0,"cross_split":0} for s in expected}
    for i, day in enumerate(dates):
        split = _split(day)
        if i < 30: excluded[split]["history"] += 1
        elif i+h > len(dates): excluded[split]["incomplete"] += 1
        elif any(_split(d) != split for d in dates[i:i+h]): excluded[split]["cross_split"] += 1
        else: expected[split].append(i)
    for split, indices in expected.items():
        batch = result["splits"][split]
        if np.asarray(batch["target_indices"]).tolist() != indices or batch["num_samples"] != len(indices):
            raise ValueError(f"Missing/extra/reordered eligible samples: {split}")
        for field,key in [("excluded_insufficient_history","history"),("excluded_incomplete_targets","incomplete"),("excluded_cross_split_targets","cross_split")]:
            if batch[field] != excluded[split][key]: raise ValueError(f"Wrong exclusion count: {split}/{field}")
        for inp,target in zip(batch["inputs"],batch["targets"]):
            if not all(d <= inp["forecast_origin"] for d in inp["input_dates"]): raise ValueError("Future input date")
            if not all(d > inp["forecast_origin"] for d in target["target_dates"]): raise ValueError("Target not after origin")
    contract = validate_window_result(result,data,scaler)
    examples = []
    for split,batch in result["splits"].items():
        for position in sorted(set([0,len(batch["inputs"])-1])):
            if not batch["inputs"]: continue
            inp,target = batch["inputs"][position],batch["targets"][position]
            examples.append({"split":split,"position":position,"sample_id":inp["sample_id"],"origin":inp["forecast_origin"],
                             "input_dates":inp["input_dates"],"input_prices_usd":inp["input_values"].ravel().tolist(),
                             "target_dates":target["target_dates"],"target_prices_usd":target["target_values"].tolist()})
    return {"passed":True,"forecast_length":h,"split_counts":contract["split_counts"],"exclusions":excluded,
            "independent_target_coverage":True,"all_input_dates_before_targets":True,"hand_check_examples":examples}
