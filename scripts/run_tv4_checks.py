"""Run TV4 tests from the workspace, retaining environment and source evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata as packages
import json
import os
from pathlib import Path
import site
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-clean', action='store_true')
    args = parser.parse_args()
    folder = ROOT / 'logs/audit' / ('tv4_tests_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(ROOT))
    names = ['torch', 'numpy', 'pandas', 'yaml', 'pytest', 'nbformat', 'nbclient', 'ipykernel']
    origins = {name: str(Path(importlib.import_module(name).__file__).resolve()) for name in names}
    config = (Path(sys.prefix) / 'pyvenv.cfg').read_text(encoding='utf-8') if (Path(sys.prefix) / 'pyvenv.cfg').is_file() else ''
    clean = (sys.prefix != sys.base_prefix and site.ENABLE_USER_SITE is False
             and 'include-system-site-packages = false' in config
             and all(Path(path).is_relative_to(Path(sys.prefix).resolve()) for path in origins.values()))
    lock = ROOT / 'scripts/requirements-tv4-lock.txt'
    mismatches = []
    for line in lock.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, expected = line.split('==', 1)
        actual = packages.version(name)
        if actual != expected:
            mismatches.append({'package': name, 'expected': expected, 'actual': actual})
    cpu_build = importlib.import_module('torch').version.cuda is None
    entrypoints = ['backend.training.trainer', 'backend.experiments.runner.experiment_runner',
                   'backend.experiments.management.experiment_manager']
    modules = {name: str(Path(importlib.import_module(name).__file__).resolve()) for name in entrypoints}
    expected_paths = [ROOT / (name.replace('.', '/') + '.py') for name in entrypoints]
    correct_imports = all(Path(modules[name]) == expected.resolve() for name, expected in zip(entrypoints, expected_paths))
    paths = [p for relative in ['backend/training', 'backend/experiments/runner', 'backend/experiments/management', 'tests/training']
             for p in (ROOT / relative).glob('*.py')]
    paths += list((ROOT / 'experiments/configs').glob('lstm_*_baseline.yaml')) + [lock, Path(__file__), ROOT / 'scripts/check_tv4_float64.py']
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    check = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    (folder / 'pip-check.log').write_text(check.stdout + check.stderr, encoding='utf-8')
    freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze', '--all'], capture_output=True, text=True, check=True)
    (folder / 'requirements-freeze.txt').write_text(freeze.stdout, encoding='utf-8')
    command = [sys.executable, '-X', 'utf8', '-m', 'pytest', 'tests/training', '-q', '-p', 'no:cacheprovider', f'--junitxml={folder / "junit.xml"}']
    env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONIOENCODING='utf-8')
    env.pop('PYTHONPATH', None)
    run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
    (folder / 'pytest.log').write_text(run.stdout + run.stderr, encoding='utf-8')
    counts = dict.fromkeys(['tests', 'failures', 'errors', 'skipped'], 0)
    if (folder / 'junit.xml').is_file():
        for suite in ET.parse(folder / 'junit.xml').getroot().iter('testsuite'):
            for key in counts:
                counts[key] += int(suite.get(key, '0'))
    unchanged = all(digest(ROOT / name) == value for name, value in hashes.items())
    intake_path = ROOT / 'logs/audit/tv4_item1_20261125/intake.json'
    intake = json.loads(intake_path.read_text(encoding='utf-8')) if intake_path.is_file() else None
    protected_changes = [name for name, value in intake['protected_hashes'].items() if not (ROOT / name).is_file() or digest(ROOT / name) != value] if intake else None
    authorized = {}
    for name in ('TV4_Item7_Source_Changes.json', 'TV5_Item2_Source_Changes.json'):
        authorized_path = ROOT / 'reports/audits' / name
        if authorized_path.is_file():
            authorized.update(json.loads(authorized_path.read_text(encoding='utf-8')))
    unexpected_changes = [name for name in protected_changes or []
                          if authorized.get(name) != digest(ROOT / name)]
    passed = (run.returncode == 0 and counts['tests'] > 0 and not any(counts[k] for k in ['failures', 'errors', 'skipped'])
              and unchanged and correct_imports and check.returncode == 0 and not unexpected_changes)
    if args.require_clean:
        passed = passed and clean and cpu_build and not mismatches
    summary = {'passed': passed, 'scope': 'TV4 items 1-4 unit and run lifecycle tests. Real-data probes are separate.',
               'counts': counts, 'command': command, 'exit_code': run.returncode,
               'executable': sys.executable, 'python': sys.version, 'prefix': sys.prefix, 'base_prefix': sys.base_prefix,
               'clean_environment': clean, 'require_clean': args.require_clean, 'user_site_enabled': site.ENABLE_USER_SITE,
               'cpu_torch_build': cpu_build, 'module_origins': origins, 'entrypoint_origins': modules, 'workspace_imports': correct_imports,
               'lock_sha256': digest(lock), 'lock_mismatches': mismatches, 'pip_check_exit_code': check.returncode,
               'source_hashes': hashes, 'source_unchanged_during_tests': unchanged,
               'intake_evidence': str(intake_path) if intake else None, 'protected_changes_since_intake': protected_changes,
               'authorized_source_changes': authorized, 'unexpected_protected_changes': unexpected_changes,
               'known_pending': ['item10 independent reproduction and consumer acceptance'],
               'evidence': str(folder / 'summary.json')}
    (folder / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ['passed', 'counts', 'clean_environment', 'workspace_imports', 'evidence']}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
