"""Small CPU precision-cost probe on synthetic tensors; not forecasting training."""
from copy import deepcopy
from datetime import datetime,timezone
import io
import json
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.models.lstm_one_step import LSTMOneStep
from backend.models.lstm_multi_step import LSTMMultiStep
from backend.model_trace import trace_lstm


def main():
    torch.set_num_threads(1)
    results = []
    for model_type in [LSTMOneStep,LSTMMultiStep]:
        torch.manual_seed(42)
        base = model_type().cpu().eval()
        x64 = torch.randn(32,30,1,dtype=torch.float64)
        y64 = torch.randn(32,base.forecast_length,dtype=torch.float64)
        timings = {name:{"forward":[],"adam_step":[]} for name in ["float32","float64"]}
        # Alternate order to reduce systematic warmup/order bias.
        for repeat in range(5):
            order = [torch.float32,torch.float64] if repeat % 2 == 0 else [torch.float64,torch.float32]
            for dtype in order:
                model = deepcopy(base).to(dtype=dtype).eval()
                x,y = x64.to(dtype),y64.to(dtype)
                with torch.inference_mode():
                    for _ in range(3): model(x)
                    start = perf_counter()
                    for _ in range(10): prediction = model(x)
                    timings[str(dtype).split(".")[-1]]["forward"].append((perf_counter()-start)/10)
                if not torch.isfinite(prediction).all(): raise AssertionError("Nonfinite forward")
                model.train()
                optimizer = torch.optim.Adam(model.parameters(),lr=.001)
                def step():
                    optimizer.zero_grad()
                    loss = torch.nn.functional.mse_loss(model(x),y)
                    if not torch.isfinite(loss): raise AssertionError("Nonfinite loss")
                    loss.backward()
                    optimizer.step()
                for _ in range(3): step()
                start = perf_counter()
                for _ in range(10): step()
                timings[str(dtype).split(".")[-1]]["adam_step"].append((perf_counter()-start)/10)
        buffer = io.BytesIO()
        torch.save(base.state_dict(),buffer)
        buffer.seek(0)
        restored = model_type().eval()
        restored.load_state_dict(torch.load(buffer,map_location="cpu",weights_only=True))
        with torch.no_grad(): torch.testing.assert_close(restored(x64),base(x64),rtol=0,atol=0)
        trace = trace_lstm(restored,x64[:1])
        measurements = {}
        for name in timings:
            measurements[name] = {phase+"_median_seconds_per_batch":statistics.median(values) for phase,values in timings[name].items()}
            measurements[name]["raw_rounds_seconds_per_batch"] = timings[name]
        params = sum(p.numel() for p in base.parameters())
        results.append({"model":model_type.__name__,"forecast_length":base.forecast_length,"measurements":measurements,
                        "float64_over_float32_forward_ratio":measurements["float64"]["forward_median_seconds_per_batch"]/measurements["float32"]["forward_median_seconds_per_batch"],
                        "float64_over_float32_adam_ratio":measurements["float64"]["adam_step_median_seconds_per_batch"]/measurements["float32"]["adam_step_median_seconds_per_batch"],
                        "parameter_bytes":{"float32":params*4,"float64":params*8},
                        "input_tensor_bytes":{"float32":32*30*4,"float64":32*30*8},
                        "float64_state_dict_roundtrip_exact":True,"float64_trace":trace["verification"]})
    summary = {"passed":True,"torch":torch.__version__,"python":sys.version,"platform":platform.platform(),"processor":platform.processor(),
               "threads":1,"batch":32,"lookback":30,"rounds":5,"iterations_per_round":10,"warmup":3,"results":results,
               "scope":"Synthetic local CPU microbenchmark, randomized untrained base weights, no model selection or stock accuracy comparison.",
               "limitations":"Timing depends on CPU/backend/threads/load; parameter/input bytes exclude activations, gradients and Adam buffers. No guarantee float64 improves forecasting."}
    folder = ROOT/"logs/audit"/("tv3_precision_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    (folder/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"passed":True,"results":results,"evidence":str(folder/"summary.json")},indent=2))


if __name__ == "__main__": main()
