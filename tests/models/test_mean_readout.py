import torch
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_one_step.mean_readout import LSTMMeanReadout


def test_same_parameters_initialization_and_explicit_mean_math():
    torch.manual_seed(42);last=LSTMOneStep()
    torch.manual_seed(42);mean=LSTMMeanReadout()
    assert sum(p.numel() for p in mean.parameters())==4513
    assert all(torch.equal(v,mean.state_dict()[k]) for k,v in last.state_dict().items())
    x=torch.linspace(-.1,.1,60,dtype=torch.float64).reshape(2,30,1)
    sequence,_=mean.lstm(x,mean._initial_state(x))
    torch.testing.assert_close(mean(x),mean.fc(sequence.mean(1)),rtol=0,atol=0)
    assert mean(x).shape==(2,1) and mean(x).dtype==torch.float64


def test_backward_reaches_early_sequence_and_state_is_independent():
    torch.manual_seed(123);model=LSTMMeanReadout()
    x=torch.randn(2,30,1,dtype=torch.float64,requires_grad=True)
    model(x).square().mean().backward()
    assert x.grad[:,0,:].abs().sum()>0
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    model.eval()
    with torch.no_grad():torch.testing.assert_close(model(x[:1]),model(x)[:1],rtol=1e-12,atol=1e-12)
