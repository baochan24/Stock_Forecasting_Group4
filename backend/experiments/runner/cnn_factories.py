"""CNN factories reuse TV4 data validation and the shared trainer."""
from copy import deepcopy

from backend.models.cnn_one_step import CNNOneStep, CNNOneStepConfig
from backend.experiments.runner.aapl_factories import validate_aapl_config
from backend.experiments.runner.cnn_data import make_cnn_comparison_loaders
from backend.training.trainer import _validate_config


def comparison_reference(config):
    """Adapt only the config schema for the existing LSTM data consumer."""
    if config['model_type'] != 'cnn_one_step':
        raise ValueError('Expected cnn_one_step')
    CNNOneStepConfig(**config['model']).validate()
    if config['data']['lookback'] != 30 or config['data'].get('common_history') is not True:
        raise ValueError('CNN comparison requires lookback30 and common_history=true')
    reference = deepcopy(config)
    reference['model_type'] = 'lstm_one_step'
    reference['model'] = dict(input_size=1, hidden_size=32, num_layers=1, output_size=1)
    validate_aapl_config(reference)
    _validate_config(config)
    return reference


def make_cnn_model(config):
    comparison_reference(config)
    return CNNOneStep.from_config(config['model'])


def make_cnn_loaders(config, seed, *, project_root):
    return make_cnn_comparison_loaders(comparison_reference(config), seed, project_root=project_root)
