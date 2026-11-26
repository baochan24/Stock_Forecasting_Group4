from copy import deepcopy
import json
from pathlib import Path

import pytest

from backend.experiments.runner.cnn_plan import validate_official_plan
from backend.experiments.runner.experiment_runner import load_experiment_config

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('section,key,value',[
    ('model','conv1_channels',32),('training','max_epochs',101),
    ('training','learning_rate',.002),('data','prepared_id','wrong'),
    (None,'seeds',[42]),('runtime','torch_threads',2),
])
def test_changed_official_config_rejected(section,key,value):
    config=load_experiment_config(ROOT/'experiments/configs/cnn_one_step_baseline.yaml')
    plan=json.loads((ROOT/'experiments/configs/cnn_one_step_option_a.lock.json').read_text())
    assert validate_official_plan(config,plan)
    altered=deepcopy(config)
    if section is None: altered[key]=value
    else: altered[section][key]=value
    with pytest.raises(ValueError,match='locked Option A'):
        validate_official_plan(altered,plan)


def test_modified_plan_fingerprint_rejected():
    config=load_experiment_config(ROOT/'experiments/configs/cnn_one_step_baseline.yaml')
    plan=json.loads((ROOT/'experiments/configs/cnn_one_step_option_a.lock.json').read_text())
    plan['semantic_config']['training']['max_epochs']=101
    with pytest.raises(ValueError,match='fingerprint'):
        validate_official_plan(config,plan)
