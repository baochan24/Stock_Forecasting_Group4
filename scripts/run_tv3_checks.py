"""Run TV3 LSTM tests from the project root, retaining evidence and source hashes."""
from datetime import datetime,timezone
import argparse
from pathlib import Path
import hashlib
import importlib.metadata as metadata
import json
import os
import site
import importlib
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-clean',action='store_true',help='Fail if venv/package origins/lock or CPU build do not match.')
    args=parser.parse_args()
    folder = ROOT/"logs/audit"/("tv3_tests_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    origins={}
    for name in ['torch','numpy','pandas','sklearn','nbformat','nbclient','ipykernel','matplotlib']:
        module=importlib.import_module(name)
        origins[name]=str(Path(module.__file__).resolve())
    cfg=Path(sys.prefix)/'pyvenv.cfg'
    config=cfg.read_text(encoding='utf-8') if cfg.is_file() else ''
    clean=(sys.prefix != sys.base_prefix and site.ENABLE_USER_SITE is False
           and 'include-system-site-packages = false' in config
           and all(Path(p).is_relative_to(Path(sys.prefix).resolve()) for p in origins.values()))
    lock=ROOT/'scripts/requirements-tv3-lock.txt'
    mismatches=[]
    for line in lock.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'): continue
        name,wanted=line.split('==',1)
        actual=metadata.version(name)
        if actual != wanted: mismatches.append({'package':name,'expected':wanted,'actual':actual})
    cpu_build=importlib.import_module('torch').version.cuda is None
    pip_check=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True)
    (folder/'pip-check.log').write_text(pip_check.stdout+pip_check.stderr,encoding='utf-8')
    freeze=subprocess.run([sys.executable,'-m','pip','freeze','--all'],capture_output=True,text=True,check=True)
    (folder/'requirements-freeze.txt').write_text(freeze.stdout,encoding='utf-8')
    paths = list((ROOT/"backend/models/lstm_one_step").glob("*.py"))+list((ROOT/"backend/models/lstm_multi_step").glob("*.py"))
    paths += list((ROOT/"backend/model_trace").glob("*.py"))+list((ROOT/"tests/models").glob("test_lstm*.py"))
    paths += [ROOT/"tests/models/conftest.py",ROOT/"backend/data/preparation/tensors.py",ROOT/"backend/artifacts/lstm_checkpoint.py"]
    hashes = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    command = [sys.executable,"-X","utf8","-m","pytest","tests/models","-q","-p","no:cacheprovider",f"--junitxml={folder/'junit.xml'}"]
    env = dict(os.environ,OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",PYTHONIOENCODING="utf-8")
    run = subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8")
    (folder/"pytest.log").write_text(run.stdout+run.stderr,encoding="utf-8")
    suites = ET.parse(folder/"junit.xml").getroot().iter("testsuite") if (folder/"junit.xml").is_file() else []
    counts = {k:0 for k in ["tests","failures","errors","skipped"]}
    for suite in suites:
        for key in counts: counts[key] += int(suite.get(key,"0"))
    unchanged = all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == digest for p,digest in hashes.items())
    passed = run.returncode == 0 and counts["tests"] > 0 and not any(counts[k] for k in ["failures","errors","skipped"]) and unchanged
    if args.require_clean: passed=passed and clean and not mismatches and cpu_build and pip_check.returncode == 0
    summary = {"passed":passed,"exit_code":run.returncode,"counts":counts,"source_hashes":hashes,"source_unchanged":unchanged,
               "python":sys.version,"executable":sys.executable,"cpu_thread_env":{"OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1"},
               "packages":{n:metadata.version(n) for n in ["torch","pytest","numpy"]},
               "clean_environment":clean,"require_clean":args.require_clean,"prefix":sys.prefix,"base_prefix":sys.base_prefix,
               "user_site_enabled":site.ENABLE_USER_SITE,"module_origins":origins,"lock_mismatches":mismatches,
               "lock_sha256":hashlib.sha256(lock.read_bytes()).hexdigest(),"cpu_torch_build":cpu_build,"pip_check_exit_code":pip_check.returncode,
               "scope":"TV3 models/trace and synthetic TV2 adapter tests; clean-env certification requires --require-clean, real artifacts checked separately. Not model training."}
    (folder/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"passed":passed,"counts":counts,"evidence":str(folder/"summary.json")},indent=2))
    return 0 if passed else 1


if __name__ == "__main__": sys.exit(main())
