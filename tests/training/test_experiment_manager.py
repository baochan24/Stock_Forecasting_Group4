
import csv
import random
from datetime import datetime

import numpy as np
import pytest
import torch
import yaml

from backend.experiments.management import experiment_manager as manager


def test_random_seed_reproducible():
    manager.set_random_seed(42)

    first = (
        random.random(),
        np.random.rand(),
        torch.rand(1).item(),
    )

    manager.set_random_seed(42)

    second = (
        random.random(),
        np.random.rand(),
        torch.rand(1).item(),
    )

    assert first == second


def test_generate_run_id():
    timestamp = datetime(2026, 11, 20, 10, 30, 22)

    run_id = manager.generate_run_id(
        model_type="lstm_one_step",
        experiment_name="baseline",
        seed=42,
        timestamp=timestamp,
    )

    assert run_id == (
        "lstm_one_step__baseline__seed42__20261120_103022"
    )


def test_create_run_directory(tmp_path):
    config = {
        "experiment_name": "lstm_one_step_baseline",
        "model_type": "lstm_one_step",
        "seeds": [42, 123, 456],
    }

    run_dir = manager.create_run_directory(
        run_id="test_run_001",
        log_dir=str(tmp_path),
        config=config,
    )

    assert run_dir.exists()
    assert (run_dir / "config.yaml").exists()
    assert (run_dir / "predictions").is_dir()
    assert (run_dir / "metrics").is_dir()
    assert (run_dir / "audit").is_dir()

    with open(run_dir / "config.yaml", encoding="utf-8") as file:
        saved_config = yaml.safe_load(file)

    assert saved_config == config

    with pytest.raises(FileExistsError):
        manager.create_run_directory(
            "test_run_001",
            str(tmp_path),
            config,
        )


def test_save_epoch_logs(tmp_path):
    logs = [
        {
            "epoch": 1,
            "train_loss": 0.05,
            "val_loss": 0.04,
        },
        {
            "epoch": 2,
            "train_loss": 0.03,
            "val_loss": 0.02,
        },
    ]

    output = manager.save_epoch_logs(logs, tmp_path)

    assert output.exists()

    with output.open(encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["epoch"] == "1"
    assert float(rows[1]["val_loss"]) == 0.02
    assert "train_loss" in reader.fieldnames
    assert "val_loss" in reader.fieldnames

def test_seed_reproducibility():
    """Same seed must produce the same random values."""

    manager.set_random_seed(123)

    first_python = random.random()
    first_numpy = np.random.rand()
    first_torch = torch.rand(5)

    manager.set_random_seed(123)

    second_python = random.random()
    second_numpy = np.random.rand()
    second_torch = torch.rand(5)

    assert first_python == second_python
    assert first_numpy == second_numpy
    assert torch.equal(first_torch, second_torch)


def test_epoch_logs_csv_format(tmp_path):
    """CSV must contain all required fields and correct rows."""

    logs = [
        {
            "epoch": 1,
            "train_loss": 0.05,
            "val_loss": 0.04,
            "learning_rate": 0.001,
            "time_seconds": 2.5,
        },
        {
            "epoch": 2,
            "train_loss": 0.03,
            "val_loss": 0.02,
            "learning_rate": 0.001,
            "time_seconds": 2.3,
        },
    ]

    output = manager.save_epoch_logs(logs, tmp_path)

    assert output.exists()

    with output.open(encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        assert reader.fieldnames == [
            "epoch",
            "train_loss",
            "val_loss",
            "learning_rate",
            "time_seconds",
        ]

    assert len(rows) == 2
    assert rows[0]["epoch"] == "1"
    assert float(rows[1]["val_loss"]) == 0.02
