"""Versioned CNN weights and provenance. Selection belongs to the trainer.

Hashes detect corruption, not authenticity. Load only trusted handoff files.
This is an inference/best-model artifact, not an optimizer-resume checkpoint.
"""
import hashlib
import json
import math
from pathlib import Path
import re

import torch

from backend.models.cnn_one_step import CNNOneStep, CNNOneStepConfig
from backend.data.validation.validator import compute_sha256

IDENTITIES = ('dataset_version', 'scaler_id', 'prepared_id')
PROVENANCE = (*IDENTITIES, 'source_hashes', 'scaler_manifest_sha256', 'prepared_manifest_sha256')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _metadata(meta, architecture):
    if not isinstance(meta, dict) or type(meta.get('trained')) is not bool:
        raise ValueError('Explicit trained status required')
    for key in (*IDENTITIES, 'run_id'):
        if not isinstance(meta.get(key), str) or not re.fullmatch('[A-Za-z0-9_-]+', meta[key]):
            raise ValueError(f'Invalid {key}')
    hashes = meta.get('source_hashes', {})
    if set(hashes) != {'raw','metadata','validated','validation_report','quality_audit'} or not all(_hash(v) for v in hashes.values()):
        raise ValueError('Expected five TV1 source hashes')
    if not all(_hash(meta.get(k)) for k in ('scaler_manifest_sha256','prepared_manifest_sha256')):
        raise ValueError('Expected pinned scaler/prepared manifest hashes')
    sources = meta.get('source_files_sha256')
    if not isinstance(sources, dict) or not sources or not all(isinstance(k,str) and _hash(v) for k,v in sources.items()):
        raise ValueError('Expected source code/config hashes')
    if type(meta.get('seed')) is not int:
        raise ValueError('Explicit integer seed required')
    if meta.get('purpose') not in ('research', 'diagnostic'):
        raise ValueError('Explicit research/diagnostic purpose required')
    if meta['purpose'] == 'research' and not meta['trained']:
        raise ValueError('Research checkpoint must be trained')
    config = meta.get('training_config', {})
    data = config.get('data', {})
    if config.get('model_type') != 'cnn_one_step' or config.get('model') != architecture:
        raise ValueError('Training config architecture mismatch')
    if data.get('lookback') != 30 or data.get('forecast_length') != 1 or data.get('common_history') is not True:
        raise ValueError('Training config data mode mismatch')
    if any(data.get(k) != meta[k] for k in (*IDENTITIES,'scaler_manifest_sha256','prepared_manifest_sha256')):
        raise ValueError('Training config provenance mismatch')
    if meta['seed'] not in config.get('seeds', []):
        raise ValueError('Seed not in training config')
    if meta['trained']:
        loss = meta.get('best_val_loss')
        if (meta.get('selected_on') != 'validation' or type(meta.get('best_epoch')) is not int
                or meta['best_epoch'] < 1 or type(loss) not in (int,float) or not math.isfinite(loss) or loss < 0):
            raise ValueError('Expected validation selection, positive epoch and finite loss')
        if meta['best_epoch'] > config.get('training', {}).get('max_epochs', 0):
            raise ValueError('Best epoch exceeds training budget')
    elif meta.get('selected_on') is not None or meta.get('best_epoch',0) != 0 or meta.get('best_val_loss') is not None:
        raise ValueError('Initialized diagnostic cannot claim validation selection')


def _state(state):
    if not isinstance(state,dict) or not state or any(
        not isinstance(v,torch.Tensor) or v.device.type != 'cpu' or v.dtype != torch.float64
        or not torch.isfinite(v).all() for v in state.values()
    ):
        raise ValueError('Expected finite CPU float64 state')


def save_cnn_checkpoint(model, output_root, checkpoint_id, metadata):
    if type(model) is not CNNOneStep:
        raise TypeError('Expected CNNOneStep')
    if not isinstance(checkpoint_id,str) or not re.fullmatch('[A-Za-z0-9_-]+',checkpoint_id):
        raise ValueError('Unsafe checkpoint ID')
    architecture = model.get_config()
    _metadata(metadata, architecture)
    state = model.state_dict()
    _state(state)
    manifest = dict(format_version=1,checkpoint_id=checkpoint_id,model_type='cnn_one_step',
                    config=architecture,dtype='float64',device='cpu',metadata=metadata,
                    training_config_sha256=fingerprint(metadata['training_config']))
    # Validate JSON before creating an immutable artifact directory.
    fingerprint(manifest)
    folder = Path(output_root) / checkpoint_id
    folder.mkdir(parents=True,exist_ok=False)
    with (folder / 'weights.pt').open('xb') as stream:
        torch.save(state,stream)
    manifest['weights_sha256'] = compute_sha256(folder / 'weights.pt')
    with (folder / 'manifest.json').open('x',encoding='utf-8') as stream:
        json.dump(manifest,stream,indent=2,allow_nan=False)
    return folder


def load_cnn_checkpoint(folder, *, expected_provenance, expected_model_config,
                        expected_training_config_sha256, expected_run_id=None,
                        expected_seed=None, allow_diagnostic=False):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if (type(manifest.get('format_version')) is not int or manifest['format_version'] != 1
            or manifest.get('checkpoint_id') != folder.name or manifest.get('model_type') != 'cnn_one_step'
            or manifest.get('dtype') != 'float64' or manifest.get('device') != 'cpu'):
        raise ValueError('Checkpoint format/model/dtype mismatch')
    config = manifest.get('config', {})
    CNNOneStepConfig(**config).validate()
    if config != expected_model_config:
        raise ValueError('Checkpoint architecture mismatch')
    meta = manifest.get('metadata', {})
    _metadata(meta, config)
    if set(expected_provenance) != set(PROVENANCE) or any(meta[k] != expected_provenance[k] for k in PROVENANCE):
        raise ValueError('Checkpoint provenance mismatch')
    actual_config_hash = fingerprint(meta['training_config'])
    if (actual_config_hash != manifest.get('training_config_sha256')
            or actual_config_hash != expected_training_config_sha256):
        raise ValueError('Checkpoint training config fingerprint mismatch')
    if expected_run_id is not None and meta['run_id'] != expected_run_id:
        raise ValueError('Checkpoint run mismatch')
    if expected_seed is not None and meta['seed'] != expected_seed:
        raise ValueError('Checkpoint seed mismatch')
    if (not meta['trained'] or meta['purpose'] == 'diagnostic') and not allow_diagnostic:
        raise ValueError('Diagnostic checkpoint is not a research model')
    if compute_sha256(folder / 'weights.pt') != manifest.get('weights_sha256'):
        raise ValueError('Checkpoint checksum mismatch')
    state = torch.load(folder / 'weights.pt',map_location='cpu',weights_only=True)
    _state(state)
    model = CNNOneStep.from_config(config)
    model.load_state_dict(state,strict=True)
    return model.eval(), manifest
