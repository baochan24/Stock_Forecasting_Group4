from copy import deepcopy
from pathlib import Path

import pytest
import torch
import yaml
from torch.utils.data import DataLoader, TensorDataset

from backend.experiments.runner.cnn_factories import make_cnn_model, comparison_reference
from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments
from backend.training import trainer

ROOT = Path(__file__).resolve().parents[2]


def config():
    return load_experiment_config(str(ROOT / 'experiments/configs/cnn_one_step_baseline.yaml'))


def loader():
    x = torch.linspace(-1, 1, 33 * 30, dtype=torch.float64).reshape(33, 30, 1)
    y = torch.linspace(0, 1, 33, dtype=torch.float64).reshape(33, 1)
    return DataLoader(TensorDataset(x, y), batch_size=32, shuffle=False, drop_last=False)


@pytest.mark.parametrize('section,key,value', [
    ('data', 'forecast_length', 5), ('data', 'lookback', 60),
    ('data', 'common_history', False), ('model', 'output_size', 5),
    ('training', 'optimizer', 'sgd'),
])
def test_invalid_cnn_experiment(section, key, value):
    c = config()
    c[section][key] = value
    with pytest.raises(ValueError):
        comparison_reference(c)


def test_cnn_validation_weighted_loss_no_grad_and_tail():
    model = make_cnn_model(config()).eval()
    batches = loader()
    observed = []
    handle = model.register_forward_pre_hook(lambda m, args: observed.append(
        (len(args[0]), torch.is_grad_enabled(), m.training)))
    before = {k: v.clone() for k, v in model.state_dict().items()}
    actual = trainer._run_epoch(model, batches, torch.nn.MSELoss())
    handle.remove()
    assert observed == [(32, False, False), (1, False, False)]
    with torch.inference_mode():
        x, y = batches.dataset.tensors
        expected = (model(x) - y).square().mean().item()
    assert actual == pytest.approx(expected, rel=1e-12, abs=1e-14)
    assert all(torch.equal(before[k], v) for k, v in model.state_dict().items())
    assert all(p.grad is None for p in model.parameters())


def test_cnn_real_training_early_stop_restores_best(monkeypatch):
    c = config()
    c['training']['max_epochs'] = 5
    c['training']['early_stopping']['patience'] = 2
    model = make_cnn_model(c)
    original = trainer._run_epoch
    selected = {}
    count = 0
    def epoch(m, batches, criterion, optimizer=None, gradient_clipping=None):
        nonlocal count
        value = original(m, batches, criterion, optimizer, gradient_clipping)
        if optimizer is None:
            count += 1
            if count == 1:
                selected.update({k: v.clone() for k, v in m.state_dict().items()})
            return 1.0  # controlled plateau, not a model performance measurement
        return value
    monkeypatch.setattr(trainer, '_run_epoch', epoch)
    result = trainer.train_model(model, loader(), loader(), c, None, 'cnn_synthetic')
    assert result['early_stopped'] and result['best_epoch'] == 1
    assert len(result['epoch_logs']) == 3 and result['checkpoint_path'] is None
    assert all(torch.equal(v, selected[k]) for k, v in model.state_dict().items())


def test_runner_selects_cnn_factory_and_ram_mode(tmp_path):
    c = config()
    c['training']['max_epochs'] = 1
    c['seeds'] = [42]
    c['output']['log_dir'] = str(tmp_path / 'runs')
    c['output']['checkpoint_dir'] = str(tmp_path / 'checkpoints')
    path = tmp_path / 'cnn.yaml'
    path.write_text(yaml.safe_dump(c), encoding='utf-8')
    with pytest.raises(ValueError, match='provenance before training'):
        run_experiments(str(path), dataloader_factory=lambda cfg, seed: (loader(), loader()))
    result = run_experiments(str(path), dataloader_factory=lambda cfg, seed: (loader(), loader()),
                             persist_checkpoint=False)
    assert len(result) == 1 and result[0]['checkpoint_path'] is None
    assert result[0]['best_epoch'] == 1
    assert list((tmp_path / 'runs').rglob('metadata.json'))


def test_config_reference_preserves_data_and_caller():
    c = config()
    before = deepcopy(c)
    reference = comparison_reference(c)
    assert reference['data'] == c['data'] and c == before
    assert make_cnn_model(c).count_parameters() == 17057
