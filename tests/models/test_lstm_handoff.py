"""Persistence handoff on synthetic untrained models; no research checkpoint."""
import json
import pytest
import torch
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.artifacts.lstm_checkpoint import save_lstm_checkpoint,load_lstm_checkpoint
from backend.data.validation.validator import compute_sha256


@pytest.fixture(params=[LSTMOneStep,LSTMMultiStep])
def checkpoint(request,tmp_path):
    model=request.param().eval()
    hashes={k:'a'*64 for k in ['raw','metadata','validated','validation_report','quality_audit']}
    meta={'dataset_version':'fixture','source_hashes':hashes,'scaler_id':'scaler','run_id':'synthetic_test','trained':False}
    folder=save_lstm_checkpoint(model,tmp_path,'diagnostic',meta)
    def load(**changes):
        args=dict(expected_dataset_version='fixture',expected_source_hashes=hashes,expected_scaler_id='scaler',expected_forecast_length=model.forecast_length,allow_diagnostic=True)
        args.update(changes)
        return load_lstm_checkpoint(folder,**args)
    return model,folder,meta,load


def test_checkpoint_roundtrip_and_diagnostic_rejected_by_default(checkpoint):
    model,folder,meta,load=checkpoint
    with pytest.raises(ValueError,match='Untrained'): load(allow_diagnostic=False)
    restored,manifest=load()
    assert not restored.training and not manifest['metadata']['trained']
    x=torch.randn(2,30,1,dtype=torch.float64)
    with torch.no_grad(): torch.testing.assert_close(model(x),restored(x),rtol=0,atol=0)


def test_wrong_checkpoint_identity_or_mode_rejected(checkpoint):
    model,_,_,load=checkpoint
    for changes in [{'expected_dataset_version':'other'},{'expected_source_hashes':{}},{'expected_scaler_id':'wrong'},
                    {'expected_forecast_length':5 if model.forecast_length==1 else 1},{'expected_lookback':60}]:
        with pytest.raises(ValueError): load(**changes)


def test_bad_hash_and_silent_float32_conversion_rejected(checkpoint):
    model,folder,_,load=checkpoint
    torch.save({k:v.float() for k,v in model.state_dict().items()},folder/'weights.pt')
    with pytest.raises(ValueError,match='checksum'): load()
    path=folder/'manifest.json'; manifest=json.loads(path.read_text())
    manifest['weights_sha256']=compute_sha256(folder/'weights.pt')
    path.write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError,match='dtype'): load()


def test_checkpoint_existing_id_does_not_overwrite(checkpoint):
    model,folder,meta,_=checkpoint
    before=compute_sha256(folder/'weights.pt')
    with pytest.raises(FileExistsError): save_lstm_checkpoint(model,folder.parent,folder.name,meta)
    assert compute_sha256(folder/'weights.pt')==before


def test_false_training_claim_without_selection_metadata_rejected(checkpoint):
    model,folder,meta,_=checkpoint
    bad=dict(meta,trained=True)
    with pytest.raises(ValueError,match='validation'): save_lstm_checkpoint(model,folder.parent,'invalid',bad)
    assert not (folder.parent/'invalid').exists()
