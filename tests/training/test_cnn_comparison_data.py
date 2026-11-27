from copy import deepcopy
from pathlib import Path
import pytest

from backend.experiments.runner.experiment_runner import load_experiment_config
from backend.experiments.runner.cnn_data import make_cnn_comparison_loaders


@pytest.mark.parametrize('field,value', [('lookback',60), ('forecast_length',5), ('common_history',False)])
def test_rejects_a_different_comparison_population(field,value,tmp_path):
    root = Path(__file__).resolve().parents[2]
    config = deepcopy(load_experiment_config(root/'experiments/configs/lstm_one_step_baseline.yaml'))
    config['data'].update(common_history=True)
    config['data'][field] = value
    with pytest.raises(ValueError,match='comparison requires'):
        make_cnn_comparison_loaders(config,42,project_root=tmp_path)
