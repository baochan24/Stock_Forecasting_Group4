
"""Training and validation module for Stock Forecasting Group 4."""

import copy
import logging
import math
import time
from pathlib import Path

import torch
from torch import nn

from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep

logger = logging.getLogger(__name__)


def _model_contract(model):
    """Validate, never silently migrate or cast model parameters."""
    floating = [p for p in model.parameters() if p.is_floating_point()]
    if not floating:
        raise TypeError("Model must have floating-point parameters.")
    if any(p.device.type != "cpu" for p in model.parameters()):
        raise ValueError("Training requires CPU model parameters.")
    dtype = floating[0].dtype
    if any(p.dtype != dtype for p in floating):
        raise TypeError("Model parameters must have a consistent dtype.")
    is_lstm = isinstance(model, (LSTMOneStep, LSTMMultiStep))
    if is_lstm:
        if dtype != torch.float64:
            raise TypeError("Project LSTM training requires float64 parameters.")
        if model.input_size != 1 or model.forecast_length not in (1, 5):
            raise ValueError("Project LSTM requires one feature and horizon 1 or 5.")
    return dtype, is_lstm


def _read_batch(batch, *, model):
    """Preserve tensor precision; reject incompatible dtype/device/shape."""
    if isinstance(batch, (tuple, list)) and len(batch) >= 2:
        inputs, targets = batch[0], batch[1]
    elif isinstance(batch, dict) and "inputs" in batch and "targets" in batch:
        inputs, targets = batch["inputs"], batch["targets"]
    else:
        raise TypeError("Batch must contain inputs and targets.")

    dtype, is_lstm = _model_contract(model)
    inputs = torch.as_tensor(inputs)
    targets = torch.as_tensor(targets)

    for name, tensor in (("Inputs", inputs), ("Targets", targets)):
        if tensor.device.type != "cpu":
            raise ValueError(f"{name} must be on CPU.")
        if not tensor.is_floating_point() or tensor.dtype != dtype:
            raise TypeError(f"{name} dtype must match model dtype {dtype}; no implicit cast.")
        if not torch.isfinite(tensor).all():
            raise ValueError(f"{name} contains NaN or Inf.")

    if inputs.ndim < 2 or targets.ndim < 2:
        raise ValueError("Inputs and targets must have at least 2 dimensions.")

    if inputs.shape[0] != targets.shape[0]:
        raise ValueError("Input and target batch sizes do not match.")

    if inputs.shape[0] == 0:
        raise ValueError("Batch must not be empty.")
    if is_lstm:
        if inputs.ndim != 3 or inputs.shape[1] not in (10, 30, 60) or inputs.shape[2] != 1:
            raise ValueError("LSTM inputs must have shape (B, T, 1), T=10/30/60; default 30.")
        if targets.shape != (inputs.shape[0], model.forecast_length):
            raise ValueError("LSTM target shape must be (B, forecast_length), matching model horizon.")

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
    def check_weights():
        for name, parameter in model.named_parameters():
            if not torch.isfinite(parameter.detach()).all():
                raise FloatingPointError(f"Non-finite weight: {name}")

    check_weights()

    total_loss = 0.0
    total_samples = 0
    horizon_sums = None

    context = torch.enable_grad() if is_training else torch.no_grad()

    with context:
        for batch in data_loader:
            inputs, targets = _read_batch(batch, model=model)

            if is_training:
                optimizer.zero_grad(set_to_none=True)

            predictions = model(inputs)

            if predictions.dtype != targets.dtype or predictions.device != targets.device:
                raise TypeError("Output dtype/device must match target; no implicit promotion.")

            if predictions.shape != targets.shape:
                raise ValueError(
                    f"Output shape {tuple(predictions.shape)} "
                    f"does not match target shape {tuple(targets.shape)}."
                )

            loss = criterion(predictions, targets)
            if not is_training:
                values = (predictions - targets).square().sum(dim=0).detach()
                horizon_sums = values if horizon_sums is None else horizon_sums + values

            if not torch.isfinite(loss).item():
                raise FloatingPointError("Non-finite loss detected.")

            if is_training:
                loss.backward()
                for name, parameter in model.named_parameters():
                    if parameter.grad is not None and not torch.isfinite(parameter.grad).all():
                        raise FloatingPointError(f"Non-finite gradient: {name}")

                if gradient_clipping is not None:
                    torch.nn.utils.clip_grad_norm_(
                        model.parameters(),
                        max_norm=gradient_clipping,
                        error_if_nonfinite=True,
                    )

                optimizer.step()
                check_weights()

            batch_size = inputs.shape[0]
            total_loss += loss.item() * batch_size
            total_samples += batch_size

    if total_samples == 0:
        raise ValueError("DataLoader is empty.")

    epoch_loss = total_loss / total_samples
    if not math.isfinite(epoch_loss):
        raise FloatingPointError("Non-finite epoch loss.")
    if not is_training:
        criterion.val_mse_per_horizon = (horizon_sums / total_samples).tolist()
    return epoch_loss


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
    *,
    on_epoch=None,
    checkpoint_saver=None,
):
    """Restore the validation best in memory; checkpoint_dir=None selects RAM only."""
    if not isinstance(model, nn.Module):
        raise TypeError("model must be a PyTorch nn.Module.")

    if not isinstance(run_id, str):
        raise TypeError("run_id must be a string.")

    if not run_id.strip() or Path(run_id).name != run_id:
        raise ValueError("Invalid run_id.")

    if checkpoint_dir is not None and not isinstance(checkpoint_dir, str):
        raise TypeError("checkpoint_dir must be a string.")

    (
        max_epochs,
        learning_rate,
        patience,
        gradient_clipping,
    ) = _validate_config(config)

    if checkpoint_saver is not None and not callable(checkpoint_saver):
        raise TypeError("checkpoint_saver must be callable.")
    if checkpoint_dir is not None and checkpoint_saver is None:
        raise ValueError("checkpoint_dir requires checkpoint_saver; use run_experiments for verified LSTM persistence.")
    checkpoint_path = None

    _model_contract(model)

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

        train_seconds = time.perf_counter() - epoch_start
        validation_start = time.perf_counter()
        val_loss = _run_epoch(
            model,
            val_loader,
            criterion,
        )

        validation_seconds = time.perf_counter() - validation_start
        epoch_seconds = time.perf_counter() - epoch_start
        current_lr = float(optimizer.param_groups[0]["lr"])

        epoch_logs.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "learning_rate": current_lr,
            "time_seconds": epoch_seconds,
            "train_seconds": train_seconds,
            "validation_seconds": validation_seconds,
            "val_mse_per_horizon": getattr(criterion, "val_mse_per_horizon", []),
        })
        if on_epoch is not None:
            on_epoch(epoch_logs)

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

            if checkpoint_saver is not None:
                checkpoint_path = Path(checkpoint_saver(model, epoch, val_loss))

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
        "checkpoint_path": str(checkpoint_path) if checkpoint_path is not None else None,
        "epoch_logs": epoch_logs,
        "total_time_seconds": total_time_seconds,
        "early_stopped": early_stopped,
    }
