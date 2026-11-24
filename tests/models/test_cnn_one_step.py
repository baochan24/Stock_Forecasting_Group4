import pytest
import torch

from backend.models.cnn_one_step import CNNOneStep, CNNOneStepConfig


def test_forward_shape():
    model = CNNOneStep().eval()
    assert model(torch.randn(8, 30, 1)).shape == (8, 1)


def test_rejects_wrong_input_shape():
    model = CNNOneStep()
    for bad in (torch.randn(8, 29, 1), torch.randn(8, 30), torch.randn(8, 30, 2)):
        with pytest.raises(ValueError):
            model(bad)


def test_deterministic_in_eval_with_seed():
    torch.manual_seed(0)
    a = CNNOneStep().eval()
    torch.manual_seed(0)
    b = CNNOneStep().eval()
    x = torch.randn(4, 30, 1)
    assert torch.allclose(a(x), b(x))


def test_samples_are_independent():
    model = CNNOneStep().eval()
    x = torch.randn(5, 30, 1)
    assert torch.allclose(model(x)[2:3], model(x[2:3]), atol=1e-6)


def test_gradients_flow():
    model = CNNOneStep()
    model(torch.randn(4, 30, 1)).sum().backward()
    assert all(p.grad is not None for p in model.parameters())


def test_config_roundtrip_and_param_count():
    model = CNNOneStep()
    clone = CNNOneStep.from_config(model.get_config())
    assert clone.count_parameters() == model.count_parameters() > 0


def test_invalid_config():
    with pytest.raises(ValueError):
        CNNOneStep(CNNOneStepConfig(kernel_size=4))