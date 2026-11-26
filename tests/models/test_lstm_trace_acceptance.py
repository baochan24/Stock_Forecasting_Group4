"""TV3 item4: trace after update/reload, schema and failure detection."""
import json
from unittest.mock import patch
import pytest
import torch
from backend.model_trace import trace_lstm
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep


@pytest.fixture(params=[LSTMOneStep,LSTMMultiStep])
def model(request):
    torch.manual_seed(42)
    return request.param().cpu().eval()


def test_trace_after_update_disk_reload_json_and_preserved_gradients(model,tmp_path):
    x = torch.randn(1,30,1,dtype=torch.float64,requires_grad=True)
    x_before = x.detach().clone()
    initial = trace_lstm(model,x)
    optimizer = torch.optim.Adam(model.parameters(),lr=.001)
    model.train(); optimizer.zero_grad()
    model(x).square().mean().backward(); optimizer.step(); model.eval()
    weights = {k:v.clone() for k,v in model.state_dict().items()}
    grads = [p.grad.clone() if p.grad is not None else None for p in model.parameters()]
    input_grad = x.grad.clone()
    after = trace_lstm(model,x)
    assert initial['prediction_scaled'] != after['prediction_scaled']
    assert after['verification']['rtol'] == 1e-10 and after['verification']['atol'] == 1e-12
    checkpoint = tmp_path/'synthetic_state.pt'
    torch.save(model.state_dict(),checkpoint)
    restored = type(model)().eval()
    restored.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True),strict=True)
    assert trace_lstm(restored,x) == after
    artifact = tmp_path/'trace.json'
    artifact.write_text(json.dumps(after,allow_nan=False),encoding='utf-8')
    assert json.loads(artifact.read_text(encoding='utf-8')) == after
    for key,value in model.state_dict().items(): torch.testing.assert_close(value,weights[key],rtol=0,atol=0)
    for parameter,before in zip(model.parameters(),grads): torch.testing.assert_close(parameter.grad,before,rtol=0,atol=0)
    torch.testing.assert_close(x.grad,input_grad,rtol=0,atol=0)
    torch.testing.assert_close(x.detach(),x_before,rtol=0,atol=0)
    assert not model.training and not model.lstm.training and not model.fc.training


def test_trace_schema_and_first_step_recurrence(model):
    x = torch.linspace(-1,1,30,dtype=torch.float64).reshape(1,30,1)
    trace = trace_lstm(model,x)
    assert set(trace) == {'trace_type','input_shape','input_scaled','output_shape','prediction_scaled','initial_hidden','initial_cell','steps','linear_input','verification'}
    assert trace['trace_type'] == 'reconstructed_and_verified'
    assert trace['input_shape'] == [1,30,1] and trace['output_shape'] == [1,model.forecast_length]
    assert set(trace['verification']) == {'passed','rtol','atol','max_hidden_abs_error','max_cell_abs_error','max_prediction_abs_error'}
    for index,step in enumerate(trace['steps'],1):
        assert set(step) == {'time_step','input_gate','forget_gate','candidate_state','output_gate','hidden_state','cell_state'}
        assert step['time_step'] == index
        assert all(len(step[key]) == 32 for key in step if key != 'time_step')
    first = trace['steps'][0]
    i,g,o,c,h = [torch.tensor(first[k],dtype=torch.float64) for k in ['input_gate','candidate_state','output_gate','cell_state','hidden_state']]
    torch.testing.assert_close(c,i*g,rtol=1e-10,atol=1e-12)  # c0=0
    torch.testing.assert_close(h,o*torch.tanh(c),rtol=1e-10,atol=1e-12)


@pytest.mark.parametrize('state_index',[0,1])
def test_trace_rejects_hidden_or_cell_reference_mismatch(model,state_index):
    original = model.lstm.forward
    def altered(values,hx=None):
        sequence,states = original(values,hx)
        if values.shape[1] == 1:
            modified = list(states); modified[state_index] = modified[state_index]+.01
            return sequence,tuple(modified)
        return sequence,states
    with patch.object(model.lstm,'forward',side_effect=altered):
        with pytest.raises(RuntimeError,match='Trace mismatch'):
            trace_lstm(model,torch.zeros(1,30,1,dtype=torch.float64))


@pytest.mark.parametrize('child',['lstm','fc'])
def test_trace_rejects_training_child_without_changing_mode(model,child):
    getattr(model,child).train()
    with pytest.raises(ValueError,match='eval'):
        trace_lstm(model,torch.zeros(1,30,1,dtype=torch.float64))
    assert not model.training and getattr(model,child).training
