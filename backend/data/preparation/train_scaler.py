"""Fit exactly one train scaler from an accepted full TV1 snapshot."""
from datetime import datetime, timezone
from pathlib import Path
import platform

from backend.artifacts.scaler import save_scaler
from backend.data.preparation.preparation import create_split_plan, fit_scaler
from backend.data.preparation.snapshot import load_tv1_snapshot


def build_train_scaler(project_root, dataset_version, *, scaler_id=None):
    """Accept snapshot → select train by date → fit once → save new artifact.

    Validation/test are never passed to fit. Inference uses load_scaler only.
    Returns scaler, manifest directory, accepted snapshot and split plan.
    """
    snapshot = load_tv1_snapshot(project_root, dataset_version)
    plan = create_split_plan(snapshot["data"])
    train = plan["data"].iloc[plan["target_indices"]["train"]]
    scaler = fit_scaler(train.adjusted_close.to_numpy())
    now = datetime.now(timezone.utc)
    metadata = {"dataset_version":dataset_version,"source_hashes":snapshot["acceptance"]["hashes"],
                "fit_split":"train","feature":"adjusted_close","currency":"USD",
                "fit_first_date":str(train.date.iloc[0]),"fit_last_date":str(train.date.iloc[-1]),
                "fit_row_count":len(train),"fit_once_per_build":True,
                "created_at_utc":now.isoformat(),"python_version":platform.python_version(),
                "train_selection":"2015-01-01 <= date <= 2022-12-31; no windows"}
    identifier = scaler_id or "aapl_scaler_" + now.strftime("%Y%m%dT%H%M%S%fZ")
    folder = save_scaler(scaler,metadata,Path(project_root)/"artifacts/scalers",identifier)
    return {"scaler":scaler,"folder":folder,"snapshot":snapshot,"plan":plan}
