
"""Experiment management utilities for Stock Forecasting Group 4."""

import csv
import json
import platform
import random
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import yaml


def set_random_seed(seed: int) -> None:
    """Set random seeds for reproducible experiments."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def generate_run_id(
    model_type: str,
    experiment_name: str,
    seed: int,
    timestamp: datetime | None = None,
) -> str:
    """Generate a run ID following the project naming convention."""
    if not model_type or not experiment_name:
        raise ValueError("Model type and experiment name are required.")

    if any(c in model_type + experiment_name for c in "/\\"):
        raise ValueError("Names must not contain path separators.")

    timestamp = timestamp or datetime.now()
    time_part = timestamp.strftime("%Y%m%d_%H%M%S")

    return (
        f"{model_type}__{experiment_name}"
        f"__seed{seed}__{time_part}"
    )


def create_run_directory(
    run_id: str,
    log_dir: str,
    config: dict,
) -> Path:
    """Create a run directory and save its configuration."""
    if not run_id or Path(run_id).name != run_id:
        raise ValueError("Invalid run_id.")

    run_dir = Path(log_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    for folder in ("predictions", "metrics", "audit"):
        (run_dir / folder).mkdir()

    config_path = run_dir / "config.yaml"

    with config_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            config,
            file,
            allow_unicode=True,
            sort_keys=False,
        )

    return run_dir


def save_epoch_logs(
    epoch_logs: list[dict],
    run_dir: str | Path,
) -> Path:
    """Save training history to epoch_logs.csv."""
    columns = [
        "epoch",
        "train_loss",
        "val_loss",
        "learning_rate",
        "time_seconds",
    ]

    output_path = Path(run_dir) / "epoch_logs.csv"

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for log in epoch_logs:
            writer.writerow({
                column: log.get(column, "")
                for column in columns
            })

    return output_path


def _get_git_info() -> tuple[str | None, bool | None]:
    """Get the current Git commit and working-tree status."""
    project_root = Path(__file__).resolve().parents[3]

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        return commit, bool(status.strip())

    except (subprocess.SubprocessError, FileNotFoundError):
        return None, None


def save_run_metadata(
    run_id: str,
    config: dict,
    metrics: dict,
    path: str | Path,
    seed: int,
    start_time: datetime | None = None,
    dataset_hash: str | None = None,
    scaler_path: str | None = None,
) -> Path:
    """Save experiment environment and training results as JSON."""
    end_time = datetime.now()
    start_time = start_time or end_time

    git_commit, git_dirty = _get_git_info()

    metadata = {
        "run_id": run_id,
        "experiment_name": config.get("experiment_name"),
        "model_type": config.get("model_type"),
        "seed": seed,
        "dataset_version": config.get("data", {}).get(
            "dataset_version"
        ),
        "dataset_hash": dataset_hash,
        "scaler_path": scaler_path,
        "checkpoint_path": metrics.get("checkpoint_path"),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_time_seconds": metrics.get("total_time_seconds"),
        "best_epoch": metrics.get("best_epoch"),
        "best_val_loss": metrics.get("best_val_loss"),
        "early_stopped": metrics.get("early_stopped"),
        "hostname": platform.node(),
        "cpu_info": platform.processor() or platform.machine(),
    }

    output_path = Path(path) / "metadata.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    return output_path
