import pytest
import torch

from backend.models.cnn_one_step import CNNOneStep, CNNOneStepConfig


@pytest.mark.parametrize('field,value', [
    ('lookback', 10), ('n_features', 2), ('output_size', 5), ('output_size', True),
    ('conv1_channels', 0), ('conv2_channels', -1), ('kernel_size', 0),
    ('kernel_size', 4), ('pool_size', 31), ('hidden_units', 1.5),
    ('dropout', float('nan')), ('dropout', float('inf')), ('dropout', True),
    ('dropout', -.1), ('dropout', 1.),
])
def test_invalid_contract_config(field, value):
    with pytest.raises(ValueError):
        CNNOneStep(CNNOneStepConfig(**{field: value}))


def test_precision_and_shape_without_global_dtype_change():
    before = torch.get_default_dtype()
    model = CNNOneStep().eval()
    assert torch.get_default_dtype() == before
    assert model.count_parameters() == 17057
    assert all(p.dtype == torch.float64 and p.device.type == 'cpu' for p in model.parameters())
    with torch.no_grad():
        assert model(torch.zeros(1, 30, 1, dtype=torch.float64)).shape == (1, 1)
    with pytest.raises(TypeError, match='float64'):
        model(torch.zeros(1, 30, 1, dtype=torch.float32))


@pytest.mark.parametrize('value', [float('nan'), float('inf')])
def test_nonfinite_input_rejected(value):
    with pytest.raises(ValueError, match='finite'):
        CNNOneStep()(torch.full((1,30,1), value, dtype=torch.float64))


def test_empty_batch_rejected():
    with pytest.raises(ValueError, match='nonempty'):
        CNNOneStep()(torch.empty(0,30,1,dtype=torch.float64))
