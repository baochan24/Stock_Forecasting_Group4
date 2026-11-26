"""Run all TV2 tests and retain actual test log, environment and source hashes."""
from datetime import datetime,timezone
import io
import json
from pathlib import Path
import site
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data.validation.validator import compute_sha256


def main():
    output = ROOT/"logs/audit"/("tv2_tests_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    output.mkdir(parents=True,exist_ok=False)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT/"tests/data"),pattern="test_tv2*.py")
    result = unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (output/"unittest.log").write_text(stream.getvalue(),encoding="utf-8")
    freeze = subprocess.run([sys.executable,"-m","pip","freeze"],capture_output=True,text=True,check=True)
    (output/"requirements-freeze.txt").write_text(freeze.stdout,encoding="utf-8")
    sources = list((ROOT/"backend/data").rglob("*.py"))+list((ROOT/"backend/artifacts").glob("*.py"))+list((ROOT/"backend/audit").glob("*.py"))+list((ROOT/"tests/data").glob("test_tv2*.py"))
    passed = result.wasSuccessful() and not result.skipped and result.testsRun > 0
    summary = {"passed":passed,"tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skips":len(result.skipped),
               "python":sys.version,"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,"user_site_enabled":site.ENABLE_USER_SITE,
               "source_hashes":{p.relative_to(ROOT).as_posix():compute_sha256(p) for p in sources}}
    (output/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"passed":passed,"tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skips":len(result.skipped),"evidence":str(output/"summary.json")},indent=2))
    return 0 if passed else 1


if __name__ == "__main__": sys.exit(main())
