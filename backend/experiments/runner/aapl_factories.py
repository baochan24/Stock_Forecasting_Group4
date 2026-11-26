"""Build TV4's train and validation loaders from the accepted TV2 handoff."""
from pathlib import Path
import re

import torch
from torch.utils.data import DataLoader, Dataset

from backend.artifacts.prepared import load_prepared_modes
from backend.artifacts.scaler import load_scaler
from backend.audit.tv2_leakage import audit_temporal_windows, audit_train_statistics
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.tensors import make_lstm_training_batch
from backend.data.validation.validator import compute_sha256
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep


HORIZONS = {"lstm_one_step": 1, "lstm_multi_step": 5}


def validate_aapl_config(config):
    data, model = config["data"], config["model"]
    h = HORIZONS.get(config["model_type"])
    if h is None or type(data["forecast_length"]) is not int or data["forecast_length"] != h:
        raise ValueError("LSTM model_type and forecast_length must match")
    if data["ticker"] != "AAPL" or type(data["lookback"]) is not int or data["lookback"] not in (10,30,60):
        raise ValueError("Prepared windows require AAPL with lookback 10, 30 or 60")
    for key, wanted in (("input_size", 1), ("num_layers", 1), ("output_size", h)):
        value = model.get(key, wanted)
        if type(value) is not int or value != wanted:
            raise ValueError(f"Invalid {key} for {config['model_type']}")
    for value in (model["hidden_size"], config["training"]["batch_size"]):
        if type(value) is not int or value < 1:
            raise ValueError("hidden_size and batch_size must be positive integers")
    for key in ("scaler_id", "prepared_id", "dataset_version"):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(data.get(key, ""))):
            raise ValueError(f"Invalid {key}")
    for key in ("scaler_manifest_sha256", "prepared_manifest_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(data.get(key, ""))):
            raise ValueError(f"Expected pinned {key}")


def make_aapl_model(config):
    validate_aapl_config(config)
    cls = LSTMOneStep if config["model_type"] == "lstm_one_step" else LSTMMultiStep
    return cls(input_size=1, hidden_size=config["model"]["hidden_size"]).cpu()


class ForecastDataset(Dataset):
    """The third batch field retains the sample ID alongside X and y."""

    def __init__(self, packed, provenance):
        self.X = packed["X"]
        self.y = packed["y"]
        self.sample_ids = tuple(packed["sample_ids"])
        self.origins = tuple(row["forecast_origin"] for row in packed["inputs"])
        self.target_dates = tuple(tuple(row["target_dates"]) for row in packed["targets"])
        self.provenance = provenance

    def __len__(self):
        return len(self.sample_ids)

    def __getitem__(self, index):
        return self.X[index], self.y[index], self.sample_ids[index]


def make_aapl_loaders(config, seed, *, project_root):
    validate_aapl_config(config)
    root = Path(project_root)
    data = config["data"]
    version, h = data["dataset_version"], data["forecast_length"]
    scaler_path = root / "artifacts/scalers" / data["scaler_id"]
    prepared_path = root / "data/prepared" / data["prepared_id"]
    for folder, key in ((scaler_path, "scaler_manifest_sha256"), (prepared_path, "prepared_manifest_sha256")):
        if compute_sha256(folder / "manifest.json") != data[key]:
            raise ValueError(f"Mismatch for {key}")
    snapshot = load_tv1_snapshot(root, version)
    hashes = snapshot["acceptance"]["hashes"]
    expected = dict(expected_dataset_version=version, expected_source_hashes=hashes)
    scaler, manifest = load_scaler(scaler_path, **expected)
    audit_train_statistics(snapshot["data"], scaler, manifest["metadata"])
    modes, prepared = load_prepared_modes(prepared_path, expected_scaler_id=manifest["scaler_id"], expected_lookback=data["lookback"], **expected)
    audit_temporal_windows(modes[h], snapshot["data"], scaler)
    provenance = dict(dataset_version=version, source_hashes=hashes, scaler_id=manifest["scaler_id"],
                      prepared_id=prepared["prepared_id"], scaler_path=scaler_path.relative_to(root).as_posix(),
                      scaler_manifest_sha256=data["scaler_manifest_sha256"], prepared_manifest_sha256=data["prepared_manifest_sha256"])
    loaders = []
    if data.get("common_history", False):
        import numpy as np
        from backend.data.preparation.contracts import validate_window_result
        for batch in modes[h]["splits"].values():
            keep = np.flatnonzero(batch["target_indices"] >= 60)
            for key in ("inputs", "targets"):
                batch[key] = [batch[key][i] for i in keep]
            for key in ("X", "y", "target_indices"):
                batch[key] = batch[key][keep]
            batch["num_samples"] = len(keep)
        validate_window_result(modes[h], snapshot["data"], scaler)
    for split in ("train", "val"):
        packed = make_lstm_training_batch(modes[h]["splits"][split], scaler, dataset_version=version, forecast_length=h)
        if packed["split"] != split:
            raise ValueError(f"Unexpected target dates for {split}")
        dataset = ForecastDataset(packed, provenance)
        loaders.append(DataLoader(dataset, batch_size=config["training"]["batch_size"], shuffle=False,
                                  drop_last=False, generator=torch.Generator().manual_seed(seed)))
    return tuple(loaders)
