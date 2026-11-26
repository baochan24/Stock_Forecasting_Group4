from pathlib import Path

import pytest

from backend.experiments.runner.aapl_factories import make_aapl_loaders, make_aapl_model
from backend.experiments.runner.experiment_runner import load_experiment_config

CONFIG = Path(__file__).resolve().parents[2] / "experiments/configs/lstm_one_step_baseline.yaml"


@pytest.mark.parametrize("section,key,value", [
    ("data", "forecast_length", 5), ("data", "lookback", 29), ("data", "ticker", "MSFT"),
    ("model", "num_layers", 2), ("model", "output_size", 5), ("training", "batch_size", 0),
])
def test_factory_rejects_incompatible_configuration(section, key, value):
    config = load_experiment_config(CONFIG)
    config[section][key] = value
    with pytest.raises(ValueError):
        make_aapl_model(config)


def test_factory_rejects_substituted_scaler_manifest(tmp_path):
    config = load_experiment_config(CONFIG)
    folder = tmp_path / "artifacts/scalers" / config["data"]["scaler_id"]
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="scaler_manifest_sha256"):
        make_aapl_loaders(config, 42, project_root=tmp_path)
