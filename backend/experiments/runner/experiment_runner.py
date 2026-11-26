
"""Experiment runner for Stock Forecasting Group 4."""

from pathlib import Path
from functools import partial
from datetime import datetime, timezone
import hashlib
import inspect
import torch

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
from backend.experiments.runner.aapl_factories import make_aapl_loaders, make_aapl_model, validate_aapl_config


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

    if config["model_type"].startswith("lstm_"):
        validate_aapl_config(config)
    return config


def run_experiments(
    config_path: str,
    model_factory=None,
    dataloader_factory=None,
    *,
    persist_checkpoint=True,
) -> list:
    """Run experiments across all configured random seeds."""

    config_path = Path(config_path).resolve()
    config = load_experiment_config(str(config_path))

    # Project root: experiments/configs/config.yaml
    project_root = Path(__file__).resolve().parents[3]
    if model_factory is None:
        model_factory = make_aapl_model
    if dataloader_factory is None:
        dataloader_factory = partial(make_aapl_loaders, project_root=project_root)

    checkpoint_dir = (
        project_root / config["output"]["checkpoint_dir"]
    )
    log_dir = (
        project_root / config["output"]["log_dir"]
    )

    torch.set_num_threads(config.get("runtime", {}).get("torch_threads", 1))
    results = []
    source_root = Path(__file__).resolve().parents[3]
    files = [Path(inspect.getfile(obj)).resolve() for obj in
             (run_experiments, create_run_directory, train_model, make_aapl_loaders)]
    files = sorted({*files, *source_root.glob("backend/**/*.py")})
    source_files = {file.relative_to(source_root).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                    for file in files}
    source_files["config_yaml"] = hashlib.sha256(config_path.read_bytes()).hexdigest()

    for seed in config["seeds"]:

        run_id = generate_run_id(
            model_type=config["model_type"],
            experiment_name=config["experiment_name"],
            seed=seed,
        )

        run_dir = create_run_directory(
            run_id,
            str(log_dir),
            config,
        )

        started = datetime.now(timezone.utc)
        metadata_args = dict(start_time=started, source_files=source_files)
        metrics = {"epoch_logs": []}

        def record_epochs(rows):
            save_epoch_logs(rows, run_dir)
            metrics["epoch_logs"] = rows
            best = min(rows, key=lambda row: row["val_loss"])
            metrics.update(best_epoch=best["epoch"], best_val_loss=best["val_loss"])

        def save_selected(model, epoch, val_loss):
            from backend.artifacts.lstm_checkpoint import save_lstm_checkpoint
            provenance = metadata_args.get("provenance")
            if provenance is None:
                raise ValueError("Checkpoint requires verified dataset provenance")
            metadata = dict(provenance, run_id=run_id, trained=True, selected_on="validation",
                            best_epoch=epoch, best_val_loss=val_loss, seed=seed, training_config=config)
            metadata["source_files_sha256"] = source_files
            saved = save_lstm_checkpoint(model, checkpoint_dir, f"{run_id}__epoch{epoch}", metadata,
                                         lookback=config["data"]["lookback"])
            metrics["checkpoint_path"] = str(saved)
            return saved

        save_epoch_logs([], run_dir)
        save_run_metadata(run_id, config, metrics, run_dir, seed, status="running", **metadata_args)
        phase = "initialization"
        try:
            set_random_seed(seed)
            model = model_factory(config)
            if not isinstance(model, nn.Module):
                raise TypeError("model_factory must return nn.Module")
            phase = "data_loading"
            train_loader, val_loader = dataloader_factory(config, seed)
            metadata_args["provenance"] = getattr(getattr(train_loader, "dataset", None), "provenance", None)
            phase = "training"
            metrics = train_model(
                model, train_loader, val_loader, config,
                None, run_id, on_epoch=record_epochs,
                checkpoint_saver=save_selected if persist_checkpoint else None,
            )
            phase = "finalization"
            save_run_metadata(run_id, config, metrics, run_dir, seed, **metadata_args)
        except (Exception, KeyboardInterrupt) as exc:
            metrics["total_time_seconds"] = (datetime.now(timezone.utc) - started).total_seconds()
            status = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
            save_run_metadata(run_id, config, metrics, run_dir, seed, status=status,
                              error={"phase": phase, "type": type(exc).__name__, "message": str(exc)}, **metadata_args)
            raise

        results.append({
            "run_id": run_id,
            "seed": seed,
            **metrics,
        })

    return results
