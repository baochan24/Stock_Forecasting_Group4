"""Create a new local source+data+scaler+prepared TV2 handoff ZIP, never upload."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.artifacts.prepared import save_prepared_modes,load_prepared_modes
from backend.artifacts.scaler import load_scaler
from backend.data.preparation.snapshot import load_tv1_snapshot
from backend.data.preparation.windows import create_one_step_windows,create_five_step_windows
from backend.audit.tv2_leakage import audit_train_statistics,audit_temporal_windows
from backend.data.validation.validator import compute_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version",required=True)
    parser.add_argument("--scaler-dir",required=True)
    args = parser.parse_args()
    snapshot = load_tv1_snapshot(ROOT,args.dataset_version)
    scaler_folder = Path(args.scaler_dir).resolve()
    scaler,manifest = load_scaler(scaler_folder,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot["acceptance"]["hashes"])
    scaler_id = manifest["scaler_id"]
    audit_train_statistics(snapshot["data"],scaler,manifest["metadata"])
    results = {1:create_one_step_windows(snapshot["data"],scaler),5:create_five_step_windows(snapshot["data"],scaler)}
    checks = [audit_temporal_windows(r,snapshot["data"],scaler) for r in results.values()]
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    prepared_id = "tv2_prepared_"+run
    prepared = save_prepared_modes(results,ROOT/"data/prepared",prepared_id,scaler_id,snapshot["acceptance"]["hashes"])
    reloaded,_ = load_prepared_modes(prepared,expected_dataset_version=args.dataset_version,expected_source_hashes=snapshot["acceptance"]["hashes"],expected_scaler_id=scaler_id)
    for result in reloaded.values(): audit_temporal_windows(result,snapshot["data"],scaler)
    bundle = ROOT/"artifacts/releases"/("TV2_Handoff_"+run)
    bundle.mkdir(parents=True,exist_ok=False)
    def copy(path, relative=None):
        target = bundle/(relative or path.relative_to(ROOT))
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    for value in snapshot["paths"].values(): copy(Path(value))
    for name in ["scaler.json","manifest.json"]: copy(scaler_folder/name,Path("artifacts/scalers")/scaler_id/name)
    for path in prepared.iterdir(): copy(path)
    sources = set((ROOT/"backend/data").rglob("*.py"))
    sources.update([ROOT/"backend/artifacts/scaler.py",ROOT/"backend/artifacts/prepared.py",ROOT/"backend/audit/tv2_leakage.py"])
    sources.update((ROOT/"tests/data").glob("test_tv2*.py"))
    sources.update((ROOT/"backend/data").rglob("README.md"))
    for name in ["build_tv2_scaler.py","inspect_tv2_input.py","inspect_tv2_split.py","check_tv2_scaling.py","check_tv2_one_step.py","check_tv2_contracts.py","audit_tv2_leakage.py","package_tv2_handoff.py","verify_tv2_handoff.py","run_tv2_checks.py","requirements-tv2-lock.txt"]:
        sources.add(ROOT/"scripts"/name)
    for name in ["rule.md","AGENTS.md","docs/TV2_Setup_and_Handoff.md","docs/04_Data_Flow_and_Contracts.md","reports/audits/TV2_PR_Audit_20261120.md"]:
        sources.add(ROOT/name)
    for path in sorted(sources): copy(path)
    # Keep actual leakage evidence with the source snapshot it describes.
    for path in (ROOT/"logs/audit").glob("tv2_leakage_*/summary.json"):
        evidence = json.loads(path.read_text(encoding="utf-8"))
        if evidence.get("dataset_version") == args.dataset_version: copy(path)
    head = subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True)
    status = subprocess.run(["git","status","--porcelain"],cwd=ROOT,capture_output=True,text=True)
    files = {p.relative_to(bundle).as_posix():compute_sha256(p) for p in bundle.rglob("*") if p.is_file()}
    handoff = {"format_version":1,"dataset_version":args.dataset_version,"prepared_id":prepared_id,"scaler_id":scaler_id,
               "git_head":head.stdout.strip() if head.returncode == 0 else None,
               "workspace_dirty":bool(status.stdout.strip()) if status.returncode == 0 else None,
               "files":files,"recipient_machine_verified":False,
               "scope":"TV2 preprocessing handoff, not a trained model release; source files include uncommitted changes."}
    with (bundle/"HANDOFF.json").open("x",encoding="utf-8") as stream: json.dump(handoff,stream,indent=2)
    archive = bundle.with_suffix(".zip")
    with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(bundle.rglob("*")):
            if path.is_file(): zipped.write(path,path.relative_to(bundle).as_posix())
    digest = compute_sha256(archive)
    with Path(str(archive)+".sha256").open("x",encoding="utf-8") as stream: stream.write(f"{digest}  {archive.name}\n")
    folder = ROOT/"logs/audit"/("tv2_package_"+run)
    folder.mkdir(parents=True,exist_ok=False)
    summary = {"passed":True,"archive":str(archive),"archive_sha256":digest,"bundle_root":str(bundle),"prepared_id":prepared_id,
               "source_hashes":snapshot["acceptance"]["hashes"],"counts":{str(h):{s:b["num_samples"] for s,b in r["splits"].items()} for h,r in results.items()},
               "recipient_machine_verified":False,"uploaded":False}
    (folder/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__": main()
