"""Synthetic diagnostics, not AAPL training or forecast quality measurements."""
import pytest
import torch

from backend.models.cnn_one_step import CNNOneStep


@pytest.mark.parametrize('batch_size', [1, 32])
def test_gradients_and_adam_update(batch_size):
    with torch.random.fork_rng():
        torch.manual_seed(42)
        model = CNNOneStep().train()
        x = torch.randn(batch_size, 30, 1, dtype=torch.float64)
        y = torch.full((batch_size, 1), 2., dtype=torch.float64)
        before = {name: p.detach().clone() for name, p in model.named_parameters()}
        optimizer = torch.optim.Adam(model.parameters(), lr=.001)
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.mse_loss(model(x), y)
        assert torch.isfinite(loss)
        loss.backward()
        for name, p in model.named_parameters():
            assert p.grad is not None, name
            assert torch.isfinite(p.grad).all(), name
            assert torch.count_nonzero(p.grad) > 0, name
        optimizer.step()
        for name, p in model.named_parameters():
            assert torch.isfinite(p).all(), name
            assert not torch.equal(before[name], p), name
        optimizer.zero_grad(set_to_none=True)
        assert all(p.grad is None for p in model.parameters())


def test_dropout_modes_and_eval_determinism():
    with torch.random.fork_rng():
        torch.manual_seed(42)
        model = CNNOneStep()
        dropout = next(m for m in model.modules() if isinstance(m, torch.nn.Dropout))
        ones = torch.ones(32, 480, dtype=torch.float64)
        model.train()
        a, b = dropout(ones), dropout(ones)
        assert dropout.training and not torch.equal(a, b)
        assert (a == 0).any() and (a != 0).any()
        torch.testing.assert_close(a[a != 0], torch.full_like(a[a != 0], 1 / .9))
        model.eval()
        assert not dropout.training
        assert torch.equal(dropout(ones), ones)
        x = torch.randn(2, 30, 1, dtype=torch.float64)
        with torch.inference_mode():
            assert torch.equal(model(x), model(x))


def test_real_file_roundtrip_after_adam(tmp_path):
    with torch.random.fork_rng():
        torch.manual_seed(123)
        model = CNNOneStep().train()
        x = torch.randn(3, 30, 1, dtype=torch.float64)
        optimizer = torch.optim.Adam(model.parameters(), lr=.001)
        model(x).square().mean().backward()
        optimizer.step()
        model.eval()
        with torch.inference_mode():
            expected = model(x).clone()
        path = tmp_path / 'cnn_diagnostic.pt'
        torch.save({'config': model.get_config(), 'state_dict': model.state_dict()}, path)
        assert path.is_file() and path.stat().st_size > 0
        saved = torch.load(path, map_location='cpu', weights_only=True)
        restored = CNNOneStep.from_config(saved['config'])
        restored.load_state_dict(saved['state_dict'], strict=True)
        restored.eval()
        assert all(p.dtype == torch.float64 for p in restored.parameters())
        with torch.inference_mode():
            torch.testing.assert_close(restored(x), expected, rtol=0, atol=0)
        bad = dict(saved['state_dict'])
        bad.pop(next(iter(bad)))
        with pytest.raises(RuntimeError, match='Missing key'):
            restored.load_state_dict(bad, strict=True)
