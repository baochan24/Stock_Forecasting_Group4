"""Audit target split assignment on an accepted TV1 snapshot, without windows."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.preparation import create_split_plan, target_split


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version", required=True)
    args = parser.parse_args()
    snapshot = load_tv1_snapshot(ROOT, args.dataset_version)
    plan = create_split_plan(snapshot["data"])
    data = plan["data"]
    splits = {}
    for name, indices in plan["target_indices"].items():
        first, last = int(indices[0]), int(indices[-1])
        history = data.iloc[max(0,first-30):first]
        splits[name] = {"row_count":len(indices), "first_target_date":str(data.iloc[first].date),
                        "last_target_date":str(data.iloc[last].date), "first_target_index":first,
                        "preceding_history_count":len(history),
                        "preceding_history_start":str(history.iloc[0].date) if len(history) else None,
                        "preceding_history_end":str(history.iloc[-1].date) if len(history) else None}
        if target_split([str(data.iloc[first].date)]) != name:
            raise ValueError("Split boundary assignment mismatch")
    summary = {"passed":True,"dataset_version":plan["dataset_version"],"rows":len(data),
               "splits":splits,"snapshot_acceptance":snapshot["acceptance"],
               "scope":"Target date assignment and full history preserved; no windows/scaler/model evaluation."}
    folder = ROOT / "logs/audit" / ("tv2_split_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    with (folder / "summary.json").open("x",encoding="utf-8") as stream:
        json.dump(summary,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:summary[k] for k in ["passed","dataset_version","rows","splits"]},ensure_ascii=False,indent=2))
    print(f"Evidence: {folder / 'summary.json'}")


if __name__ == "__main__": main()
