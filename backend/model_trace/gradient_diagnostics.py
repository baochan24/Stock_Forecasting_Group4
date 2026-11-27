"""Measure backward flow on a private model copy; never optimize caller weights."""
from copy import deepcopy
import torch


def trace_lstm_gradients(model,inputs,targets):
    if (inputs.dtype!=torch.float64 or targets.dtype!=torch.float64 or inputs.device.type!='cpu'
            or targets.device.type!='cpu' or inputs.ndim!=3 or inputs.shape[1:]!=(30,1)
            or targets.shape!=(len(inputs),model.forecast_length) or len(inputs)==0
            or not torch.isfinite(inputs).all() or not torch.isfinite(targets).all()):
        raise ValueError('Expected finite CPU64 paired (B,30,1)/(B,H)')
    private=deepcopy(model).eval()
    for p in private.parameters():p.requires_grad_(True);p.grad=None
    x=inputs.detach().clone().requires_grad_(True)
    y=targets.detach().clone()
    prediction=private(x)
    loss=(prediction-y).square().mean()
    loss.backward()
    named=dict(private.named_parameters())
    if any(p.grad is None or not torch.isfinite(p.grad).all() for p in named.values()):
        raise ValueError('Disconnected or nonfinite parameter gradient')
    def norm(values):return float(torch.sqrt(sum(v.detach().square().sum() for v in values)))
    return dict(loss_scaled_mse=float(loss.detach()),core_grad_l2=norm([p.grad for n,p in named.items() if n.startswith('lstm.')]),
        head_weight_grad_l2=norm([private.fc.weight.grad]),head_bias_grad_l2=norm([private.fc.bias.grad]),
        core_weight_l2=norm([p for n,p in named.items() if n.startswith('lstm.')]),
        head_weight_l2=norm([private.fc.weight]),head_bias_l2=norm([private.fc.bias]),
        input_grad_l2=norm([x.grad]),input_grad_l2_per_session=[norm([x.grad[:,i,:]]) for i in range(30)],
        samples=len(inputs),evaluation_mode=True,optimizer_step_performed=False)
