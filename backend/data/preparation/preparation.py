"""TV2 draft imported from PR #2, commit 245dc5c366e3d81d2dfc2f1c2df18f3ce1e9444f.

Only split_data/fit_scaler are retained. This is not the integrated pipeline:
Use load_tv1_snapshot before splitting. Train-only scaler persistence is
orchestrated by train_scaler.build_train_scaler, not this low-level helper.
Do not window each returned split independently: retain preceding history.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np
import pandas as pd
from backend.data.transforms.scaling import _finite_values

if TYPE_CHECKING:
    from sklearn.preprocessing import StandardScaler


def target_split(target_dates) -> str | None:
    """Classify 1 or 5 ordered ISO target dates; None means a split boundary.

    Invalid/out-of-scope dates raise ValueError. Session continuity belongs to
    the accepted snapshot/windowing stage; this function only assigns split.
    """
    values = pd.Series(list(target_dates), dtype="string")
    if len(values) not in (1, 5) or not values.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False).all():
        raise ValueError("Expected 1 or 5 valid YYYY-MM-DD target dates.")
    dates = pd.to_datetime(values, format="%Y-%m-%d", errors="raise")
    if not dates.is_monotonic_increasing or dates.duplicated().any():
        raise ValueError("Target dates must be unique and increasing.")
    if not dates.dt.year.between(2015, 2025).all():
        raise ValueError("Target dates must be within 2015–2025.")
    labels = np.where(dates.dt.year <= 2022, "train", np.where(dates.dt.year == 2023, "val", "test"))
    return str(labels[0]) if (labels == labels[0]).all() else None


def create_split_plan(validated_data: pd.DataFrame) -> dict:
    """Keep the full chronological series plus target row indices per split.

    Call with load_tv1_snapshot()['data']. No windows, scaler or future values
    are assembled. Indices refer to the returned full table; later windowing
    may use preceding rows from earlier splits as already observed history.
    """
    splits = split_data(validated_data)
    frames = []
    indices = {}
    offset = 0
    for label, part in splits.items():
        size = len(part["dates"])
        frames.append(pd.DataFrame({"date": part["dates"], "ticker": "AAPL",
                                   "adjusted_close": part["prices"].ravel(),
                                   "dataset_version": part["dataset_version"]}))
        indices[label] = np.arange(offset, offset + size, dtype=np.int64)
        offset += size
    return {"data": pd.concat(frames, ignore_index=True),
            "dataset_version": splits["train"]["dataset_version"], "target_indices": indices}


def split_data(validated_file_path: str | pd.DataFrame) -> dict:
    """
    Chia dữ liệu theo thời gian:
    Train: 2015-2022
    Validation: 2023
    Test: 2024-2025. Returns dict[split] with dates (ISO strings) and
    prices (N,1) float64, sorted chronologically. Requires all three splits.
    Raises ValueError for invalid dates/prices/ticker or out-of-range years.
    Accepts a CSV path or a verified DataFrame. Retains dataset_version in each
    split; use load_tv1_snapshot first to authenticate local artifact consistency.
    """

    df = (validated_file_path.copy(deep=True) if isinstance(validated_file_path, pd.DataFrame)
          else pd.read_csv(validated_file_path))

    required_columns = ["date", "ticker", "adjusted_close", "dataset_version"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    versions = df["dataset_version"]
    if (versions.isna().any() or versions.nunique() != 1
            or not versions.map(lambda x: isinstance(x, str) and bool(x.strip())).all()):
        raise ValueError("Expected one non-empty dataset_version across all rows.")

    date_text = df["date"].astype("string")
    if not date_text.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False).all():
        raise ValueError("Dates must be non-missing YYYY-MM-DD session dates.")
    df["date"] = pd.to_datetime(date_text, format="%Y-%m-%d", errors="raise")
    if df.empty or not df["date"].dt.year.between(2015, 2025).all():
        raise ValueError("Dataset must be non-empty and within 2015–2025.")
    if not df["ticker"].eq("AAPL").all():
        raise ValueError("Only ticker AAPL is supported.")
    df = df.sort_values("date").reset_index(drop=True)

    if df["date"].duplicated().any():
        raise ValueError("Duplicate dates found in dataset.")

    if df["adjusted_close"].isna().any():
        raise ValueError("Missing adjusted_close values.")

    checked_prices = _finite_values(df["adjusted_close"].to_numpy())
    if (checked_prices <= 0).any():
        raise ValueError("Prices must be positive.")

    train = df[df["date"].dt.year.between(2015, 2022)]
    val = df[df["date"].dt.year == 2023]
    test = df[df["date"].dt.year.between(2024, 2025)]

    def convert_data(data):
        return {
            "dataset_version": str(data["dataset_version"].iloc[0]),
            "dates": data["date"].dt.strftime(
                "%Y-%m-%d"
            ).tolist(),
            "prices": data["adjusted_close"].to_numpy(
                dtype=np.float64
            ).reshape(-1, 1)
        }

    if train.empty or val.empty or test.empty:
        raise ValueError("One or more dataset splits are empty.")

    return {
        "train": convert_data(train),
        "val": convert_data(val),
        "test": convert_data(test)
    }


def fit_scaler(train_prices: np.ndarray) -> StandardScaler:
    """
    Fit a new StandardScaler on positive finite prices of shape (N,) or (N,1).

    Returns a one-feature scaler. Caller must pass only train dates and
    persist/reuse the returned instance; this helper cannot verify dates.
    Uses float64 for preparation; model tensor casting belongs at its adapter.
    """

    from sklearn.preprocessing import StandardScaler

    train_prices = _finite_values(train_prices)
    if train_prices.ndim > 2 or (train_prices.ndim == 2 and train_prices.shape[1] != 1):
        raise ValueError("Train prices must have shape (N,) or (N,1).")
    if (train_prices <= 0).any():
        raise ValueError("Train prices must be positive.")
    train_prices = train_prices.reshape(-1, 1)

    scaler = StandardScaler()
    scaler.fit(train_prices)

    return scaler
