"""Persist one-feature StandardScaler as checked JSON, without pickle execution."""
import json
from pathlib import Path
import re

import numpy as np
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_is_fitted

from backend.data.validation.validator import compute_sha256


def save_scaler(scaler, metadata, output_root, scaler_id):
    """Create a new immutable directory; existing IDs are never overwritten.

    Failed writes leave an incomplete directory (not loadable); retry with a
    new ID. Manifest is written last. No training decisions belong here.
    """
    if not isinstance(scaler_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", scaler_id):
        raise ValueError("Invalid scaler_id")
    check_is_fitted(scaler)
    if not isinstance(scaler, StandardScaler) or scaler.n_features_in_ != 1 or not scaler.with_mean or not scaler.with_std:
        raise ValueError("Expected a one-feature StandardScaler with mean/std")
    folder = Path(output_root) / scaler_id
    folder.mkdir(parents=True, exist_ok=False)
    state = {"mean":scaler.mean_.tolist(), "var":scaler.var_.tolist(),
             "scale":scaler.scale_.tolist(), "n_samples_seen":int(scaler.n_samples_seen_)}
    with (folder / "scaler.json").open("x", encoding="utf-8") as stream:
        json.dump(state, stream, allow_nan=False, indent=2)
    manifest = {"format_version":1,"scaler_id":scaler_id,"class":"StandardScaler",
                "sklearn_version":sklearn.__version__,"metadata":metadata,
                "scaler_sha256":compute_sha256(folder / "scaler.json")}
    with (folder / "manifest.json").open("x",encoding="utf-8") as stream:
        json.dump(manifest,stream,allow_nan=False,indent=2)
    return folder


def load_scaler(folder, *, expected_dataset_version, expected_source_hashes):
    """Load only when the caller supplies the exact accepted snapshot identity.

    Checks local consistency, not cryptographic authenticity of both JSONs.
    Matching sklearn version is required; never calls fit.
    """
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("format_version") != 1 or manifest.get("class") != "StandardScaler"
            or manifest.get("scaler_id") != folder.name or manifest.get("sklearn_version") != sklearn.__version__):
        raise ValueError("Unsupported scaler manifest/environment")
    meta = manifest.get("metadata", {})
    if meta.get("dataset_version") != expected_dataset_version or meta.get("source_hashes") != expected_source_hashes:
        raise ValueError("Scaler snapshot version/hash mismatch")
    if meta.get("fit_split") != "train" or meta.get("feature") != "adjusted_close" or meta.get("currency") != "USD":
        raise ValueError("Invalid scaler fit contract")
    if not ("2015-01-01" <= meta.get("fit_first_date", "") <= meta.get("fit_last_date", "") <= "2022-12-31"):
        raise ValueError("Scaler fit dates must be within train")
    if compute_sha256(folder / "scaler.json") != manifest.get("scaler_sha256"):
        raise ValueError("Scaler checksum mismatch")
    state = json.loads((folder / "scaler.json").read_text(encoding="utf-8"))
    arrays = [np.asarray(state[key], dtype=np.float64) for key in ["mean","var","scale"]]
    if any(a.shape != (1,) or not np.isfinite(a).all() for a in arrays):
        raise ValueError("Invalid scaler numeric state")
    count = state.get("n_samples_seen")
    if type(count) is not int or count <= 0 or count != meta.get("fit_row_count") or arrays[1][0] < 0 or arrays[2][0] <= 0:
        raise ValueError("Invalid scaler sample count/variance/scale")
    scaler = StandardScaler()
    scaler.mean_, scaler.var_, scaler.scale_ = arrays
    scaler.n_features_in_ = 1
    scaler.n_samples_seen_ = np.int64(count)
    return scaler, manifest
