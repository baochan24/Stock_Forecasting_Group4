
import sys
import types
from pathlib import Path

import pytest
import torch
from torch import nn

from backend.training import trainer


def get_config(max_epochs=3, patience=2):
    return {
        "training": {
            "optimizer": "adam",
            "loss_function": "mse",
            "learning_rate": 0.001,
            "max_epochs": max_epochs,
            "early_stopping": {
                "patience": patience,
                "monitor": "val_loss",
                "mode": "min",
            },
        }
    }


def mock_checkpoint(monkeypatch):
    saved = []
    def saver(model, epoch, val_loss):
        saved.append({"epoch": epoch, "val_loss": val_loss})
        return Path("synthetic_checkpoint")
    return saved, saver


def test_best_checkpoint_is_saved(monkeypatch, tmp_path):
    saved, saver = mock_checkpoint(monkeypatch)

    losses = iter([
        1.0, 0.5,
        0.9, 0.3,
        0.8, 0.4,
    ])

    monkeypatch.setattr(
        trainer,
        "_run_epoch",
        lambda *args, **kwargs: next(losses),
    )

    model = nn.Linear(1, 1)

    result = trainer.train_model(
        model=model,
        train_loader=[],
        val_loader=[],
        config=get_config(max_epochs=3),
        checkpoint_dir=None,
        checkpoint_saver=saver,
        run_id="test_best",
    )

    assert result["best_epoch"] == 2
    assert result["best_val_loss"] == 0.3
    assert len(saved) == 2
    assert len(result["epoch_logs"]) == 3


def test_early_stopping(monkeypatch, tmp_path):
    _, saver = mock_checkpoint(monkeypatch)

    losses = iter([
        1.0, 0.5,
        1.0, 0.6,
        1.0, 0.7,
    ])

    monkeypatch.setattr(
        trainer,
        "_run_epoch",
        lambda *args, **kwargs: next(losses),
    )

    model = nn.Linear(1, 1)

    result = trainer.train_model(
        model=model,
        train_loader=[],
        val_loader=[],
        config=get_config(max_epochs=10, patience=2),
        checkpoint_dir=None,
        checkpoint_saver=saver,
        run_id="test_early_stop",
    )

    assert result["early_stopped"] is True
    assert result["best_epoch"] == 1
    assert len(result["epoch_logs"]) == 3


def test_multi_step_targets_supported(monkeypatch, tmp_path):
    _, saver = mock_checkpoint(monkeypatch)

    inputs = torch.randn(8, 1)
    targets = torch.randn(8, 5)

    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(inputs, targets),
        batch_size=4,
    )

    model = nn.Linear(1, 5)

    result = trainer.train_model(
        model=model,
        train_loader=loader,
        val_loader=loader,
        config=get_config(max_epochs=1, patience=1),
        checkpoint_dir=None,
        checkpoint_saver=saver,
        run_id="test_multi_step",
    )

    assert result["best_epoch"] == 1
    assert result["best_val_loss"] >= 0


def test_output_target_shape_mismatch(monkeypatch, tmp_path):
    _, saver = mock_checkpoint(monkeypatch)

    inputs = torch.randn(8, 1)
    targets = torch.randn(8, 5)

    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(inputs, targets),
        batch_size=4,
    )

    model = nn.Linear(1, 1)

    with pytest.raises(ValueError, match="Output shape"):
        trainer.train_model(
            model=model,
            train_loader=loader,
            val_loader=loader,
            config=get_config(max_epochs=1),
            checkpoint_dir=None,
        checkpoint_saver=saver,
            run_id="test_shape_error",
        )
def test_training_reduces_loss(monkeypatch, tmp_path):
    """Training must reduce loss on a small synthetic dataset."""

    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    from backend.training import trainer

    torch.manual_seed(42)

    # Create a simple dataset: y = 2x + 1
    x = torch.linspace(-1, 1, 64).reshape(-1, 1)
    y = 2 * x + 1

    loader = DataLoader(
        TensorDataset(x, y),
        batch_size=16,
        shuffle=False,
    )

    model = nn.Linear(1, 1)

    # Calculate loss before training.
    with torch.no_grad():
        initial_loss = torch.mean((model(x) - y) ** 2).item()

    _, saver = mock_checkpoint(monkeypatch)

    config = {
        "training": {
            "optimizer": "adam",
            "loss_function": "mse",
            "learning_rate": 0.05,
            "max_epochs": 50,
            "early_stopping": {
                "patience": 50,
                "monitor": "val_loss",
                "mode": "min",
            },
            "gradient_clipping": None,
        }
    }

    result = trainer.train_model(
        model=model,
        train_loader=loader,
        val_loader=loader,
        config=config,
        checkpoint_dir=None,
        checkpoint_saver=saver,
        run_id="loss_reduction_test",
    )

    assert result["best_val_loss"] < initial_loss
    assert result["best_epoch"] >= 1
    assert len(result["epoch_logs"]) > 1