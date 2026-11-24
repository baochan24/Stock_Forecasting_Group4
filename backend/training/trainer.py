
"""Training and validation module for Stock Forecasting Group 4."""

import copy
import logging
import math
import time
from pathlib import Path

import torch
from torch import nn

logger = logging.getLogger(__name__)


def _read_batch(batch):
    """Extract input and target tensors."""
    if isinstance(batch, (tuple, list)) and len(batch) >= 2:
        inputs, targets = batch[0], batch[1]
    elif isinstance(batch, dict) and "inputs" in batch and "targets" in batch:
        inputs, targets = batch["inputs"], batch["targets"]
    else:
        raise TypeError("Batch must contain inputs and targets.")

    inputs = torch.as_tensor(inputs, dtype=torch.float32, device="cpu")
    targets = torch.as_tensor(targets, dtype=torch.float32, device="cpu")

    if inputs.ndim < 2 or targets.ndim < 2:
        raise ValueError("Inputs and targets must have at least 2 dimensions.")

    if inputs.shape[0] != targets.shape[0]:
        raise ValueError("Input and target batch sizes do not match.")

    return inputs, targets


def _run_epoch(
    model,
    data_loader,
    criterion,
    optimizer=None,
    gradient_clipping=None,
):
    """Run one training or validation epoch."""
    is_training = optimizer is not None
    model.train(is_training)

    total_loss = 0.0
    total_samples = 0

    context = torch.enable_grad() if is_training else torch.no_grad()

    with context:
        for batch in data_loader:
            inputs, targets = _read_batch(batch)

            if is_training:
                optimizer.zero_grad(set_to_none=True)

            predictions = model(inputs)

            if predictions.shape != targets.shape:
                raise ValueError(
                    f"Output shape {tuple(predictions.shape)} "
                    f"does not match target shape {tuple(targets.shape)}."
                )

            loss = criterion(predictions, targets)

            if not torch.isfinite(loss).item():
                raise FloatingPointError("Non-finite loss detected.")

            if is_training:
                loss.backward()

                if gradient_clipping is not None:
                    torch.nn.utils.clip_grad_norm_(
                        model.parameters(),
                        max_norm=gradient_clipping,
                    )

                optimizer.step()

            batch_size = inputs.shape[0]
            total_loss += loss.item() * batch_size
            total_samples += batch_size

    if total_samples == 0:
        raise ValueError("DataLoader is empty.")

    return total_loss / total_samples


def _save_best_checkpoint(
    model,
    optimizer,
    epoch,
    val_loss,
    checkpoint_path,
):
    """Delegate checkpoint saving to TV6."""
    try:
        from backend.artifacts import save_checkpoint
    except ImportError as exc:
        raise RuntimeError(
            "TV6 must implement backend.artifacts.save_checkpoint()."
        ) from exc

    save_checkpoint(
        model,
        optimizer,
        epoch,
        val_loss,
        str(checkpoint_path),
    )


def _validate_config(config):
    """Validate training configuration."""
    if not isinstance(config, dict):
        raise TypeError("config must be a dictionary.")

    training = config.get("training")

    if not isinstance(training, dict):
        raise TypeError("training configuration must be a dictionary.")

    optimizer_name = training.get("optimizer")
    loss_name = training.get("loss_function")

    if not isinstance(optimizer_name, str):
        raise TypeError("optimizer must be a string.")

    if not isinstance(loss_name, str):
        raise TypeError("loss_function must be a string.")

    if optimizer_name.lower() != "adam":
        raise ValueError("Only Adam optimizer is supported.")

    if loss_name.lower() != "mse":
        raise ValueError("Only MSE loss is supported.")

    max_epochs = training.get("max_epochs")

    if isinstance(max_epochs, bool) or not isinstance(max_epochs, int):
        raise TypeError("max_epochs must be an integer.")

    if max_epochs < 1:
        raise ValueError("max_epochs must be positive.")

    learning_rate = training.get("learning_rate")

    if isinstance(learning_rate, bool) or not isinstance(
        learning_rate, (int, float)
    ):
        raise TypeError("learning_rate must be numeric.")

    learning_rate = float(learning_rate)

    if not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("learning_rate must be positive and finite.")

    early = training.get("early_stopping")

    if not isinstance(early, dict):
        raise TypeError("early_stopping must be a dictionary.")

    patience = early.get("patience")

    if isinstance(patience, bool) or not isinstance(patience, int):
        raise TypeError("patience must be an integer.")

    if patience < 1:
        raise ValueError("patience must be positive.")

    if early.get("monitor") != "val_loss" or early.get("mode") != "min":
        raise ValueError("Early stopping must monitor val_loss in min mode.")

    gradient_clipping = training.get("gradient_clipping")

    if gradient_clipping is not None:
        if isinstance(gradient_clipping, bool) or not isinstance(
            gradient_clipping, (int, float)
        ):
            raise TypeError("gradient_clipping must be numeric or None.")

        gradient_clipping = float(gradient_clipping)

        if not math.isfinite(gradient_clipping) or gradient_clipping <= 0:
            raise ValueError("gradient_clipping must be positive.")

    return max_epochs, learning_rate, patience, gradient_clipping


def train_model(
    model,
    train_loader,
    val_loader,
    config,
    checkpoint_dir,
    run_id,
):
    """Train a model and retain the best validation checkpoint."""
    if not isinstance(model, nn.Module):
        raise TypeError("model must be a PyTorch nn.Module.")

    if not isinstance(run_id, str):
        raise TypeError("run_id must be a string.")

    if not run_id.strip() or Path(run_id).name != run_id:
        raise ValueError("Invalid run_id.")

    if not isinstance(checkpoint_dir, str):
        raise TypeError("checkpoint_dir must be a string.")

    (
        max_epochs,
        learning_rate,
        patience,
        gradient_clipping,
    ) = _validate_config(config)

    checkpoint_directory = Path(checkpoint_dir)
    checkpoint_directory.mkdir(parents=True, exist_ok=True)

    checkpoint_path = checkpoint_directory / f"{run_id}_best.pt"

    if checkpoint_path.exists():
        raise FileExistsError(f"Checkpoint already exists: {checkpoint_path}")

    model.to(torch.device("cpu"))

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate,
    )

    criterion = nn.MSELoss()

    best_epoch = 0
    best_val_loss = float("inf")
    best_state_dict = None

    epochs_without_improvement = 0
    early_stopped = False
    epoch_logs = []

    total_start = time.perf_counter()

    for epoch in range(1, max_epochs + 1):
        epoch_start = time.perf_counter()

        train_loss = _run_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            gradient_clipping,
        )

        val_loss = _run_epoch(
            model,
            val_loader,
            criterion,
        )

        epoch_seconds = time.perf_counter() - epoch_start
        current_lr = float(optimizer.param_groups[0]["lr"])

        epoch_logs.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "learning_rate": current_lr,
            "time_seconds": epoch_seconds,
        })

        logger.info(
            "Epoch %d/%d | train_loss=%.6f | val_loss=%.6f | time=%.3fs",
            epoch,
            max_epochs,
            train_loss,
            val_loss,
            epoch_seconds,
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            best_state_dict = copy.deepcopy(model.state_dict())

            _save_best_checkpoint(
                model,
                optimizer,
                epoch,
                val_loss,
                checkpoint_path,
            )

            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= patience:
            early_stopped = True
            logger.info("Early stopping at epoch %d.", epoch)
            break

    total_time_seconds = time.perf_counter() - total_start

    if best_state_dict is None:
        raise RuntimeError("No valid best model was produced.")

    model.load_state_dict(best_state_dict)

    return {
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "checkpoint_path": str(checkpoint_path),
        "epoch_logs": epoch_logs,
        "total_time_seconds": total_time_seconds,
        "early_stopped": early_stopped,
    }
