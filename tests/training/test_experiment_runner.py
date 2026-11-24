
from pathlib import Path

import pytest
import yaml

from backend.experiments.runner.experiment_runner import (
    load_experiment_config,
)


def test_load_existing_lstm_config():
    project_root = Path(__file__).resolve().parents[2]

    config_path = (
        project_root
        / "experiments"
        / "configs"
        / "lstm_one_step_baseline.yaml"
    )

    config = load_experiment_config(str(config_path))

    assert config["model_type"] == "lstm_one_step"
    assert config["data"]["ticker"] == "AAPL"
    assert config["data"]["lookback"] == 30
    assert config["data"]["forecast_length"] == 1
    assert config["training"]["optimizer"] == "adam"
    assert config["seeds"] == [42, 123, 456]


def test_missing_config_file():
    with pytest.raises(FileNotFoundError):
        load_experiment_config("not_found.yaml")


def test_invalid_model_type(tmp_path):
    config = {
        "experiment_name": "invalid_test",
        "model_type": "transformer",
        "data": {"forecast_length": 1},
        "model": {},
        "training": {},
        "seeds": [42],
        "output": {
            "checkpoint_dir": "artifacts/checkpoints",
            "log_dir": "experiments/runs",
        },
    }

    path = tmp_path / "invalid.yaml"

    with path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(config, file)

    with pytest.raises(ValueError, match="Unsupported model_type"):
        load_experiment_config(str(path))


def test_duplicate_seeds_rejected(tmp_path):
    config = {
        "experiment_name": "duplicate_seed_test",
        "model_type": "lstm_one_step",
        "data": {"forecast_length": 1},
        "model": {},
        "training": {},
        "seeds": [42, 42],
        "output": {
            "checkpoint_dir": "artifacts/checkpoints",
            "log_dir": "experiments/runs",
        },
    }

    path = tmp_path / "duplicate.yaml"

    with path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(config, file)

    with pytest.raises(ValueError, match="seeds"):
        load_experiment_config(str(path))

def test_load_lstm_multi_step_config():
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]

    config_path = (
        project_root
        / "experiments"
        / "configs"
        / "lstm_multi_step_baseline.yaml"
    )

    config = load_experiment_config(str(config_path))

    assert config["model_type"] == "lstm_multi_step"
    assert config["data"]["ticker"] == "AAPL"
    assert config["data"]["lookback"] == 30
    assert config["data"]["forecast_length"] == 5
    assert config["model"]["hidden_size"] == 32
    assert config["training"]["optimizer"] == "adam"
    assert config["seeds"] == [42, 123, 456]
