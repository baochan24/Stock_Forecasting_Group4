
"""Experiment runner for Stock Forecasting Group 4."""

from pathlib import Path

import yaml
from torch import nn

from backend.experiments.management.experiment_manager import (
    create_run_directory,
    generate_run_id,
    save_epoch_logs,
    save_run_metadata,
    set_random_seed,
)
from backend.training.trainer import train_model


def load_experiment_config(config_path: str) -> dict:
    """Load and validate experiment configuration."""

    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise TypeError("Experiment config must be a YAML mapping.")

    required = [
        "experiment_name",
        "model_type",
        "data",
        "model",
        "training",
        "seeds",
        "output",
    ]

    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"Missing config fields: {missing}")

    if config["model_type"] not in (
        "lstm_one_step",
        "lstm_multi_step",
        "cnn_one_step",
    ):
        raise ValueError("Unsupported model_type")

    if config["data"].get("forecast_length") not in (1, 5):
        raise ValueError("forecast_length must be 1 or 5")

    seeds = config["seeds"]

    if (
        not isinstance(seeds, list)
        or not seeds
        or any(type(s) is not int for s in seeds)
        or len(seeds) != len(set(seeds))
    ):
        raise ValueError("Invalid or duplicate seeds")

    data = config["data"]
    model = config["model"]
    training = config["training"]
    early = training.get("early_stopping", {})

    if not all(k in data for k in ("ticker", "lookback", "dataset_version")):
        raise ValueError("Missing data configuration")

    if not all(k in model for k in ("input_size", "hidden_size")):
        raise ValueError("Missing model configuration")

    if not all(
        k in training
        for k in (
            "batch_size",
            "optimizer",
            "learning_rate",
            "loss_function",
            "max_epochs",
        )
    ):
        raise ValueError("Missing training configuration")

    if not all(k in early for k in ("patience", "monitor", "mode")):
        raise ValueError("Missing early stopping configuration")

    if not all(
        k in config["output"]
        for k in ("checkpoint_dir", "log_dir")
    ):
        raise ValueError("Missing output configuration")

    return config


def run_experiments(
    config_path: str,
    model_factory,
    dataloader_factory,
) -> list:
    """Run experiments across all configured random seeds."""

    config_path = Path(config_path).resolve()
    config = load_experiment_config(str(config_path))

    # Project root: experiments/configs/config.yaml
    project_root = config_path.parents[2]

    checkpoint_dir = (
        project_root / config["output"]["checkpoint_dir"]
    )
    log_dir = (
        project_root / config["output"]["log_dir"]
    )

    results = []

    for seed in config["seeds"]:

        set_random_seed(seed)

        run_id = generate_run_id(
            model_type=config["model_type"],
            experiment_name=config["experiment_name"],
            seed=seed,
        )

        model = model_factory(config)

        if not isinstance(model, nn.Module):
            raise TypeError("model_factory must return nn.Module")

        train_loader, val_loader = dataloader_factory(config, seed)

        run_dir = create_run_directory(
            run_id,
            str(log_dir),
            config,
        )

        metrics = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            config=config,
            checkpoint_dir=str(checkpoint_dir),
            run_id=run_id,
        )

        save_epoch_logs(
            metrics["epoch_logs"],
            run_dir,
        )

        save_run_metadata(
            run_id,
            config,
            metrics,
            run_dir,
            seed,
        )

        results.append({
            "run_id": run_id,
            "seed": seed,
            **metrics,
        })

    return results
