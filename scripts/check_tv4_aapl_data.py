"""Check configured TV4 data paths and both TV3 forwards on every accepted train/val window."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import torch
from torch.utils.data import SequentialSampler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.experiments.runner.experiment_runner import load_experiment_config
from backend.experiments.runner.aapl_factories import make_aapl_model, make_aapl_loaders
from backend.training.trainer import _read_batch


def check_config(path):
    config = load_experiment_config(path)
    model = make_aapl_model(config).eval()
    train, val = make_aapl_loaders(config, config["seeds"][0], project_root=ROOT)
    h = model.forecast_length
    rows = []
    for split, loader in (("train", train), ("val", val)):
        ds = loader.dataset
        assert isinstance(loader.sampler, SequentialSampler)
        offset = 0
        with torch.inference_mode():
            for batch in loader:
                x, y = _read_batch(batch, model=model)
                last_size = len(x)
                assert tuple(batch[2]) == ds.sample_ids[offset:offset + last_size]
                assert torch.equal(x, ds.X[offset:offset + last_size]) and torch.equal(y, ds.y[offset:offset + last_size])
                pred = model(x)
                assert pred.shape == y.shape and pred.dtype == torch.float64 and torch.isfinite(pred).all()
                offset += last_size
        assert offset == len(ds) and len(set(ds.sample_ids)) == offset
        rows.append(dict(split=split, horizon=h, samples=offset, batches=len(loader), final_batch=last_size,
                         first_origin=ds.origins[0], first_target=ds.target_dates[0][0], last_target=ds.target_dates[-1][-1],
                         first_sample_id=ds.sample_ids[0], last_sample_id=ds.sample_ids[-1],
                         ordered_ids_sha256=hashlib.sha256("\n".join(ds.sample_ids).encode()).hexdigest()))
    assert train.dataset.target_dates[-1][-1] < val.dataset.target_dates[0][0]
    return dict(model=config["model_type"], config_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                provenance=train.dataset.provenance, checks=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, action="append")
    args = parser.parse_args()
    paths = args.config or [ROOT / f"experiments/configs/lstm_{mode}_step_baseline.yaml" for mode in ("one", "multi")]
    torch.set_num_threads(1)
    results = [check_config(path) for path in paths]
    folder = ROOT / "logs/audit" / ("tv4_item3_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True, exist_ok=False)
    path = folder / "summary.json"
    path.write_text(json.dumps(dict(passed=True, results=results, scope="AAPL train/validation input and forward checks"), indent=2), encoding="utf-8")
    print(json.dumps(dict(passed=True, evidence=str(path))))


if __name__ == "__main__":
    main()
