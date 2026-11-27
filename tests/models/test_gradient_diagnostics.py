from copy import deepcopy
import torch
from backend.models.lstm_one_step import LSTMOneStep
from backend.model_trace.gradient_diagnostics import trace_lstm_gradients


def test_zero_head_first_backward_blocks_core_not_head_and_copy_preserves_caller():
    torch.manual_seed(42);model=LSTMOneStep()
    torch.nn.init.zeros_(model.fc.weight);torch.nn.init.zeros_(model.fc.bias)
    model.train();before=deepcopy(model.state_dict())
    x=torch.linspace(-.2,0,30,dtype=torch.float64).reshape(1,30,1)
    y=torch.full((1,1),.1,dtype=torch.float64)
    result=trace_lstm_gradients(model,x,y)
    assert result['core_grad_l2']==0 and result['input_grad_l2']==0
    assert result['head_weight_grad_l2']>0 and result['head_bias_grad_l2']>0
    assert model.training and all(p.grad is None for p in model.parameters())
    assert all(torch.equal(before[k],v) for k,v in model.state_dict().items())
    with torch.no_grad():model.fc.weight.fill_(.01)
    assert trace_lstm_gradients(model,x,y)['core_grad_l2']>0
