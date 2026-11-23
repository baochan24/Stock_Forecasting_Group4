"""LSTM persistence contract for TV4/TV6; no training/selection decisions."""
import json
from pathlib import Path
import re
import torch

from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.data.validation.validator import compute_sha256


def _metadata(metadata):
    if not isinstance(metadata,dict) or type(metadata.get('trained')) is not bool:
        raise ValueError('Explicit trained status is required')
    for key in ['dataset_version','scaler_id','run_id']:
        if not isinstance(metadata.get(key),str) or not re.fullmatch(r'[A-Za-z0-9_-]+',metadata[key]):
            raise ValueError(f'Invalid {key}')
    hashes=metadata.get('source_hashes',{})
    if set(hashes) != {'raw','metadata','validated','validation_report','quality_audit'} or any(not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v) for v in hashes.values()):
        raise ValueError('Expected all five accepted TV1 source hashes')
    if metadata['trained']:
        if metadata.get('selected_on') != 'validation' or type(metadata.get('best_epoch')) is not int or metadata['best_epoch'] < 1:
            raise ValueError('Trained checkpoint requires validation selection and best_epoch')


def save_lstm_checkpoint(model, output_root, checkpoint_id, metadata, *, lookback=30):
    """Save once; metadata comes from caller, not proof of training history.

    TV4 chooses the validation checkpoint; this module only persists/validates.
    Diagnostic saves MUST set trained=False; never label initialized weights trained.
    """
    if type(model) not in (LSTMOneStep,LSTMMultiStep): raise TypeError('Unsupported model type')
    if model.input_size != 1: raise ValueError('Project checkpoint requires one price feature')
    if not isinstance(checkpoint_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',checkpoint_id): raise ValueError('Unsafe checkpoint ID')
    if type(lookback) is not int or lookback not in (10,30,60): raise ValueError('Unsupported lookback')
    _metadata(metadata)
    state=model.state_dict()
    if any(v.dtype != torch.float64 or v.device.type != 'cpu' or not torch.isfinite(v).all() for v in state.values()):
        raise ValueError('Checkpoint must contain finite CPU float64 weights')
    config={'model_class':type(model).__name__,'input_size':model.input_size,'hidden_size':model.hidden_size,
            'forecast_length':model.forecast_length,'lookback':lookback,'num_layers':1,'dtype':'float64','device':'cpu'}
    folder=Path(output_root)/checkpoint_id
    folder.mkdir(parents=True,exist_ok=False)
    with (folder/'weights.pt').open('xb') as stream: torch.save(state,stream)
    manifest={'format_version':1,'checkpoint_id':checkpoint_id,'config':config,'metadata':metadata,
              'weights_sha256':compute_sha256(folder/'weights.pt')}
    with (folder/'manifest.json').open('x',encoding='utf-8') as stream: json.dump(manifest,stream,allow_nan=False,indent=2)
    return folder


def load_lstm_checkpoint(folder, *, expected_dataset_version, expected_source_hashes, expected_scaler_id,
                         expected_forecast_length, expected_lookback=30, allow_diagnostic=False):
    """Verify identities/hash/dtype before strict load, return an eval CPU model.

    Reject untrained artifacts by default; weights_only prevents general pickle
    object execution, but still only accept files from a trusted handoff.
    """
    folder=Path(folder)
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format_version') != 1 or manifest.get('checkpoint_id') != folder.name: raise ValueError('Wrong checkpoint format/ID')
    meta=manifest.get('metadata',{})
    _metadata(meta)
    if meta['dataset_version'] != expected_dataset_version or meta['source_hashes'] != expected_source_hashes or meta['scaler_id'] != expected_scaler_id:
        raise ValueError('Checkpoint dataset/hash/scaler mismatch')
    if not meta['trained'] and not allow_diagnostic: raise ValueError('Untrained diagnostic checkpoint is not a research model')
    config=manifest.get('config',{})
    classes={1:LSTMOneStep,5:LSTMMultiStep}
    if type(expected_forecast_length) is not int or expected_forecast_length not in classes: raise ValueError('Wrong forecast length')
    cls=classes[expected_forecast_length]
    if (config.get('model_class') != cls.__name__ or config.get('forecast_length') != expected_forecast_length
            or config.get('lookback') != expected_lookback or config.get('num_layers') != 1
            or config.get('dtype') != 'float64' or config.get('device') != 'cpu' or config.get('input_size') != 1):
        raise ValueError('Checkpoint architecture/mode/dtype mismatch')
    if compute_sha256(folder/'weights.pt') != manifest.get('weights_sha256'): raise ValueError('Checkpoint checksum mismatch')
    state=torch.load(folder/'weights.pt',map_location='cpu',weights_only=True)
    if not isinstance(state,dict) or not state or any(not isinstance(v,torch.Tensor) or v.dtype != torch.float64 or not torch.isfinite(v).all() for v in state.values()):
        raise ValueError('Wrong checkpoint state dtype/finite contract')
    model=cls(input_size=1,hidden_size=config['hidden_size'])
    model.load_state_dict(state,strict=True)
    return model.cpu().eval(),manifest
