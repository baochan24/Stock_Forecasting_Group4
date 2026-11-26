"""Synthetic identities only. These artifacts are never research models."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset
import yaml

from backend.artifacts.cnn_checkpoint import (PROVENANCE, fingerprint, load_cnn_checkpoint,
                                             save_cnn_checkpoint)
from backend.experiments.runner.experiment_runner import load_experiment_config, run_experiments
from backend.models.cnn_one_step import CNNOneStep
from backend.data.validation.validator import compute_sha256


def metadata():
    config = load_experiment_config(Path(__file__).resolve().parents[2] / 'experiments/configs/cnn_one_step_baseline.yaml')
    config['data'].update(dataset_version='synthetic_dataset',scaler_id='synthetic_scaler',prepared_id='synthetic_prepared',
                          scaler_manifest_sha256='a'*64,prepared_manifest_sha256='b'*64)
    return dict(**{k:config['data'][k] for k in PROVENANCE if k != 'source_hashes'},
        source_hashes={k:'c'*64 for k in ('raw','metadata','validated','validation_report','quality_audit')},
        run_id='synthetic_run',seed=42,trained=False,purpose='diagnostic',training_config=config,
        source_files_sha256={'fixture':'d'*64})


def expected(meta):
    return dict(expected_provenance={k:meta[k] for k in PROVENANCE},
                expected_model_config=meta['training_config']['model'],
                expected_training_config_sha256=fingerprint(meta['training_config']))


def saved(tmp_path):
    meta = metadata()
    model = CNNOneStep().eval()
    return model, meta, save_cnn_checkpoint(model,tmp_path,'diagnostic',meta)


def test_diagnostic_reload_exact_and_immutable(tmp_path):
    model, meta, folder = saved(tmp_path)
    with pytest.raises(ValueError,match='Diagnostic'):
        load_cnn_checkpoint(folder,**expected(meta))
    restored, manifest = load_cnn_checkpoint(folder,**expected(meta),allow_diagnostic=True)
    assert restored is not model and not restored.training
    x = torch.ones(2,30,1,dtype=torch.float64)
    with torch.inference_mode():
        torch.testing.assert_close(model(x),restored(x),rtol=0,atol=0)
    assert manifest['metadata']['trained'] is False
    with pytest.raises(FileExistsError):
        save_cnn_checkpoint(model,tmp_path,'diagnostic',meta)


@pytest.mark.parametrize('field',list(PROVENANCE))
def test_reject_mismatched_provenance(tmp_path,field):
    _, meta, folder = saved(tmp_path)
    args = expected(meta)
    args['expected_provenance'][field] = 'wrong'
    with pytest.raises(ValueError,match='provenance'):
        load_cnn_checkpoint(folder,**args,allow_diagnostic=True)


@pytest.mark.parametrize('field,value', [('expected_run_id','wrong'),('expected_seed',123),
    ('expected_training_config_sha256','0'*64), ('expected_model_config',{})])
def test_reject_wrong_config_run_seed(tmp_path,field,value):
    _, meta, folder = saved(tmp_path)
    args = expected(meta)
    args[field] = value
    with pytest.raises(ValueError):
        load_cnn_checkpoint(folder,**args,allow_diagnostic=True)


@pytest.mark.parametrize('damage',['checksum','float32','nan','missing_key','wrong_shape'])
def test_reject_corrupted_weights(tmp_path,damage):
    _, meta, folder = saved(tmp_path)
    path = folder / 'weights.pt'
    if damage == 'checksum':
        path.write_bytes(path.read_bytes()+b'corrupt')
    else:
        state = torch.load(path,weights_only=True)
        key = next(iter(state))
        if damage == 'float32': state[key] = state[key].float()
        if damage == 'nan': state[key].fill_(float('nan'))
        if damage == 'missing_key': state.pop(key)
        if damage == 'wrong_shape': state[key] = state[key][:0]
        torch.save(state,path)
        manifest = json.loads((folder/'manifest.json').read_text())
        manifest['weights_sha256'] = compute_sha256(path)
        (folder/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises((ValueError,RuntimeError)):
        load_cnn_checkpoint(folder,**expected(meta),allow_diagnostic=True)


@pytest.mark.parametrize('field,value',[('trained',None),('purpose','research'),('seed',True),
    ('scaler_manifest_sha256','bad'),('selected_on','validation')])
def test_invalid_metadata_does_not_create_artifact(tmp_path,field,value):
    meta = metadata()
    meta[field] = value
    with pytest.raises(ValueError):
        save_cnn_checkpoint(CNNOneStep(),tmp_path,'invalid',meta)
    assert not (tmp_path/'invalid').exists()


def test_runner_persists_selected_synthetic_diagnostic(tmp_path):
    meta = metadata()
    config = deepcopy(meta['training_config'])
    config['training']['max_epochs'] = 2
    config['seeds'] = [42]
    config['output'] = dict(checkpoint_dir=str(tmp_path/'checkpoints'),log_dir=str(tmp_path/'runs'))
    path = tmp_path/'config.yaml'
    path.write_text(yaml.safe_dump(config))
    x = torch.linspace(-1,1,33*30,dtype=torch.float64).reshape(33,30,1)
    dataset = TensorDataset(x,torch.ones(33,1,dtype=torch.float64))
    dataset.provenance = {k:meta[k] for k in PROVENANCE}
    def loaders(c, seed):
        return (DataLoader(dataset,batch_size=32),DataLoader(dataset,batch_size=32))
    result = run_experiments(str(path),dataloader_factory=loaders,checkpoint_purpose='diagnostic')[0]
    folder = Path(result['checkpoint_path'])
    m = json.loads((folder/'manifest.json').read_text())
    actual = m['metadata']
    assert actual['trained'] and actual['purpose'] == 'diagnostic'
    assert actual['best_epoch'] == result['best_epoch'] and actual['best_val_loss'] == result['best_val_loss']
    args = expected(actual)
    with pytest.raises(ValueError,match='Diagnostic'):
        load_cnn_checkpoint(folder,**args)
    restored,_ = load_cnn_checkpoint(folder,**args,expected_run_id=result['run_id'],expected_seed=42,allow_diagnostic=True)
    with torch.inference_mode():
        mse = (restored(x)-dataset.tensors[1]).square().mean().item()
    assert mse == pytest.approx(result['best_val_loss'],rel=1e-12,abs=1e-14)
    rows = json.loads(next((tmp_path/'runs').rglob('metadata.json')).read_text())
    assert rows['status'] == 'completed'


@pytest.mark.parametrize('field,value',[('best_epoch',0),('best_epoch',101),
    ('best_val_loss',float('nan')),('selected_on','test')])
def test_trained_selection_metadata_rejected(tmp_path,field,value):
    meta = metadata()
    meta.update(trained=True,best_epoch=1,best_val_loss=.5,selected_on='validation')
    meta[field] = value
    with pytest.raises(ValueError):
        save_cnn_checkpoint(CNNOneStep(),tmp_path,'bad_selection',meta)
    assert not (tmp_path/'bad_selection').exists()


def test_research_schema_acceptance_is_not_proof_of_training(tmp_path):
    # Schema fixture only: caller supplies training claims, persistence cannot prove them.
    meta = metadata()
    meta.update(trained=True,purpose='research',best_epoch=1,best_val_loss=.5,selected_on='validation')
    folder = save_cnn_checkpoint(CNNOneStep(),tmp_path,'schema_fixture',meta)
    restored,manifest = load_cnn_checkpoint(folder,**expected(meta))
    assert not restored.training and manifest['metadata']['selected_on'] == 'validation'
