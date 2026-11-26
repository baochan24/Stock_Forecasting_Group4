import csv
import json
from pathlib import Path

import pytest
import torch
from torch import nn
import yaml

from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments
from backend.training.trainer import _run_epoch


def test_direct_save_requires_callback_before_updates(tmp_path):
    from backend.training.trainer import train_model
    model = nn.Linear(1, 1)
    initial = model.weight.detach().clone()
    config = {"training": {"optimizer": "adam", "loss_function": "mse", "learning_rate": .001,
                          "max_epochs": 1, "early_stopping": {"patience": 1, "monitor": "val_loss", "mode": "min"}}}
    with pytest.raises(ValueError, match="checkpoint_saver"):
        train_model(model, [], [], config, str(tmp_path / 'unused'), 'direct')
    assert torch.equal(initial, model.weight)
    assert not (tmp_path / 'unused').exists()


def test_direct_training_with_explicit_saver(tmp_path):
    from backend.training.trainer import train_model
    model = nn.Linear(1, 1)
    x = torch.ones(3, 1)
    loader = [(x, 2*x)]
    config = {"training": {"optimizer": "adam", "loss_function": "mse", "learning_rate": .001,
                          "max_epochs": 1, "early_stopping": {"patience": 1, "monitor": "val_loss", "mode": "min"}}}
    def save(model, epoch, val_loss):
        path = tmp_path / f"epoch{epoch}.pt"
        torch.save(model.state_dict(), path)
        return path
    result = train_model(model, loader, loader, config, str(tmp_path), 'direct', checkpoint_saver=save)
    restored = nn.Linear(1, 1)
    restored.load_state_dict(torch.load(result['checkpoint_path'], weights_only=True))
    with torch.no_grad():
        torch.testing.assert_close(restored(x), model(x), rtol=0, atol=0)


def test_epoch_weights_the_short_batch_by_sample_count():
    model = nn.Linear(1, 1, bias=False)
    x = torch.zeros(3, 1)
    y = torch.tensor([[1.], [1.], [3.]])
    loader = [(x[:2], y[:2]), (x[2:], y[2:])]
    assert _run_epoch(model, loader, nn.MSELoss()) == pytest.approx(11 / 3)


@pytest.mark.parametrize('fault', ['gradient', 'weight'])
def test_nonfinite_update_is_rejected(fault):
    model = nn.Linear(1, 1)
    opt = torch.optim.Adam(model.parameters())
    if fault == 'gradient':
        model.weight.register_hook(lambda grad: torch.full_like(grad, float('inf')))
    else:
        def break_weight(*args):
            with torch.no_grad():
                model.weight.fill_(float('nan'))
        opt.register_step_post_hook(break_weight)
    batch = [(torch.ones(1, 1), torch.zeros(1, 1))]
    before = model.weight.detach().clone()
    with pytest.raises(FloatingPointError, match=fault):
        _run_epoch(model, batch, nn.MSELoss(), opt)
    if fault == 'gradient':
        assert torch.equal(before, model.weight) and not opt.state


@pytest.mark.parametrize('case', ['improves_then_worsens', 'tie', 'failure', 'interrupt'])
def test_runner_records_real_adam_updates_and_partial_history(tmp_path, case):
    root = Path(__file__).resolve().parents[2]
    config = load_experiment_config(root / 'experiments/configs/lstm_one_step_baseline.yaml')
    config['experiment_name'] = 'synthetic_run_acceptance'
    config['output']['log_dir'] = str(tmp_path / 'runs')
    config['seeds'] = [42]
    config['training'].update(learning_rate=.05, max_epochs=20)
    config['training']['early_stopping']['patience'] = 2
    path = tmp_path / 'fixture.yaml'
    path.write_text(yaml.safe_dump(config), encoding='utf-8')
    model = nn.Linear(1, 1, bias=False, dtype=torch.float64)
    with torch.no_grad():
        model.weight.zero_()
    x = torch.ones(3, 1, dtype=torch.float64)
    val_x = torch.zeros_like(x) if case == 'tie' else x
    train = [(x, x)]
    val_y = torch.full_like(x, .2)

    class Validation:
        calls = 0

        def __iter__(self):
            self.calls += 1
            if self.calls == 3 and case == 'interrupt':
                raise KeyboardInterrupt('diagnostic interruption')
            if self.calls == 3 and case == 'failure':
                yield val_x, torch.full_like(x, float('nan'))
            else:
                yield val_x, val_y

    def run():
        return run_experiments(path, lambda cfg: model, lambda cfg, seed: (train, Validation()),
                               persist_checkpoint=False)

    if case in ('failure', 'interrupt'):
        with pytest.raises(ValueError if case == 'failure' else KeyboardInterrupt):
            run()
    else:
        result, = run()
    directory, = (tmp_path / 'runs').iterdir()
    meta = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    with (directory / 'epoch_logs.csv').open(encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == meta['epochs_completed']
    assert [int(row['epoch']) for row in rows] == list(range(1, len(rows)+1))
    assert meta['start_time'] < meta['end_time'] and meta['torch_threads'] > 0
    assert meta['source_files_sha256'] and meta['seed'] == 42
    assert meta['checkpoint_path'] is None
    assert meta['best_epoch'] == int(min(rows, key=lambda row: float(row['val_loss']))['epoch'])
    if case in ('failure', 'interrupt'):
        assert len(rows) == 2
        assert meta['status'] == ('failed' if case == 'failure' else 'interrupted')
        assert meta['error']['phase'] == 'training'
    else:
        assert meta['status'] == 'completed' and meta['early_stopped']
        assert result['best_epoch'] + 2 == len(rows)
        assert float(model.weight.detach().item()) != 0
        assert model.training is False
        assert (model(val_x) - val_y).square().mean().item() == pytest.approx(meta['best_val_loss'])
        if case == 'tie':
            assert result['best_epoch'] == 1
        else:
            assert result['best_epoch'] > 1 and float(rows[-1]['val_loss']) > meta['best_val_loss']
