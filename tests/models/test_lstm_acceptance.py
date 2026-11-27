"""TV3 item3 acceptance: float64 architecture, numerical gradients and persistence.

All data are synthetic. Temporary state_dict files are test artifacts, not
trained research checkpoints or a replacement for TV4 training logic.
"""
import pytest
import torch
from torch import nn
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep


@pytest.fixture(params=[LSTMOneStep,LSTMMultiStep])
def accepted_model(request):
    torch.manual_seed(42)
    return request.param().cpu()


def test_exact_architecture_and_last_step_linear(accepted_model):
    model = accepted_model.eval()
    assert list(model.children()) == [model.lstm,model.fc]
    assert isinstance(model.lstm,nn.LSTM) and isinstance(model.fc,nn.Linear)
    assert model.lstm.input_size == 1 and model.lstm.hidden_size == 32
    assert model.lstm.num_layers == 1 and model.lstm.batch_first
    assert not model.lstm.bidirectional and model.lstm.proj_size == 0
    assert model.fc.in_features == 32 and model.fc.out_features == model.forecast_length
    x = torch.randn(3,30,1,dtype=torch.float64)
    before = x.clone()
    with torch.no_grad():
        sequence,_ = model.lstm(x,(torch.zeros(1,3,32,dtype=torch.float64),torch.zeros(1,3,32,dtype=torch.float64)))
        torch.testing.assert_close(model(x),model.fc(sequence[:,-1,:]),rtol=0,atol=0)
    torch.testing.assert_close(x,before,rtol=0,atol=0)


def test_numerical_input_and_parameter_gradients(accepted_model):
    # Tiny hidden size speeds finite differences; shared forward is unchanged.
    torch.manual_seed(42)
    model = type(accepted_model)(hidden_size=2)
    x = (torch.randn(1,3,1,dtype=torch.float64)*.1).requires_grad_()
    names,parameters = zip(*model.named_parameters())
    def forward(values,*weights):
        return torch.func.functional_call(model,dict(zip(names,weights)),(values,))
    assert torch.autograd.gradcheck(forward,(x,*parameters),eps=1e-6,atol=1e-5,rtol=1e-3,fast_mode=True)


def test_disk_reload_after_adam_update_exact(accepted_model,tmp_path):
    model = accepted_model.train()
    x = torch.randn(4,30,1,dtype=torch.float64)
    y = torch.randn(4,model.forecast_length,dtype=torch.float64)
    before = {k:v.clone() for k,v in model.state_dict().items()}
    optimizer = torch.optim.Adam(model.parameters(),lr=.001)
    optimizer.zero_grad()
    loss = nn.MSELoss()(model(x),y)
    loss.backward()
    for parameter in model.parameters():
        assert parameter.grad is not None and parameter.grad.dtype == torch.float64
        assert torch.isfinite(parameter.grad).all()
    optimizer.step()
    assert any(not torch.equal(value,before[key]) for key,value in model.state_dict().items())
    assert all(torch.isfinite(p).all() for p in model.parameters())
    path = tmp_path/"synthetic_state_dict.pt"
    torch.save(model.state_dict(),path)
    restored = type(model)().cpu()
    restored.load_state_dict(torch.load(path,map_location="cpu",weights_only=True),strict=True)
    model.eval(); restored.eval()
    for key,value in model.state_dict().items():
        assert value.dtype == restored.state_dict()[key].dtype == torch.float64
        torch.testing.assert_close(value,restored.state_dict()[key],rtol=0,atol=0)
    with torch.no_grad(): torch.testing.assert_close(model(x),restored(x),rtol=0,atol=0)


def test_eval_no_state_or_gradient_update_and_order_independent(accepted_model):
    model = accepted_model.eval()
    x = torch.randn(4,30,1,dtype=torch.float64)
    before = {k:v.clone() for k,v in model.state_dict().items()}
    with torch.inference_mode():
        output = model(x)
        individually = torch.cat([model(window.unsqueeze(0)) for window in x])
        torch.testing.assert_close(output,individually,rtol=1e-12,atol=1e-12)
        torch.testing.assert_close(model(x.flip(0)).flip(0),output,rtol=1e-12,atol=1e-12)
        assert model(x[-1:]).shape == (1,model.forecast_length)
    assert not model.training and all(p.grad is None for p in model.parameters())
    for key,value in model.state_dict().items(): torch.testing.assert_close(value,before[key],rtol=0,atol=0)


def test_wrong_horizon_checkpoint_rejected(accepted_model):
    other = LSTMMultiStep() if accepted_model.forecast_length == 1 else LSTMOneStep()
    with pytest.raises(RuntimeError,match="size mismatch"):
        accepted_model.load_state_dict(other.state_dict(),strict=True)


def test_one_and_five_step_parameters_are_not_shared():
    one,five = LSTMOneStep(),LSTMMultiStep()
    five_before = {k:v.clone() for k,v in five.state_dict().items()}
    assert {p.data_ptr() for p in one.parameters()}.isdisjoint({p.data_ptr() for p in five.parameters()})
    optimizer = torch.optim.Adam(one.parameters())
    optimizer.zero_grad()
    one(torch.ones(2,30,1,dtype=torch.float64)).square().mean().backward()
    optimizer.step()
    for key,value in five.state_dict().items(): torch.testing.assert_close(value,five_before[key],rtol=0,atol=0)
