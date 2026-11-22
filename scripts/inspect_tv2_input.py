"""Verify explicit TV1 input for TV2 and save a new read-only acceptance record."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data.preparation.snapshot import load_tv1_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version", required=True)
    args = parser.parse_args()
    snapshot = load_tv1_snapshot(ROOT, args.dataset_version)
    data = snapshot["data"]
    summary = {
        "passed": True, "dataset_version": snapshot["dataset_version"],
        "rows": len(data), "first_date": str(data.date.iloc[0]), "last_date": str(data.date.iloc[-1]),
        "columns": list(data.columns), "preview": data.head().to_dict(orient="records"),
        "acceptance": snapshot["acceptance"], "quality": snapshot["quality"], "paths": snapshot["paths"],
        "scope": "TV2 item 2: local TV1 snapshot acceptance; no scaler, windows or model training.",
    }
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "logs/audit" / f"tv2_input_{run_id}"
    folder.mkdir(parents=True, exist_ok=False)
    with (folder / "summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: summary[k] for k in ["passed", "dataset_version", "rows", "first_date", "last_date", "preview"]}, ensure_ascii=False, indent=2))
    print(f"Evidence: {folder / 'summary.json'}")


if __name__ == "__main__":
    main()
