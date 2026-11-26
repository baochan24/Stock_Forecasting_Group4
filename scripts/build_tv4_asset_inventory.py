"""Inventory current source, historical training source and accepted TV4 assets."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = set()
    for pattern in ('backend/**/*.py', 'scripts/*.py', 'scripts/requirements*',
                    'logs/audit/tv4_pre_fix_source_20261126/**/*'):
        paths.update(p for p in ROOT.glob(pattern) if p.is_file() and '__pycache__' not in p.parts)
    intake = json.loads((ROOT / 'logs/audit/tv4_item1_20261125/intake.json').read_text(encoding='utf-8'))
    paths.update(ROOT / name for name in intake['protected_hashes'] if name.startswith(('data/', 'artifacts/')))
    plan = ROOT / 'logs/audit/tv4_item7_20261125T120957429763Z'
    paths.update(plan.glob('*.yaml'))
    paths.add(plan / 'summary.json')
    for prepared in (ROOT / 'data/prepared').glob('tv4_lb*20261125T120957429763Z'):
        paths.update(p for p in prepared.iterdir() if p.is_file())
    runs = []
    for source in ('tv4_item8_20261125T122649342552Z', 'tv4_item9_20261125T140320407544Z'):
        folder = ROOT / 'logs/audit' / source
        paths.update(folder.glob('*.json'))
        paths.update(folder.glob('*.yaml'))
        summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
        for run in summary['results']:
            run_dir = folder / 'runs' / run['run_id']
            paths.update(run_dir.glob('*.*'))
            # IDs are derived from run metadata, independent of its original drive.
            epoch = run['best_epoch']
            checkpoint = ROOT / 'artifacts/checkpoints' / source / f"{run['run_id']}__epoch{epoch}"
            paths.update(checkpoint.glob('*.*'))
            runs.append(dict(run_id=run['run_id'], metadata=(run_dir / 'metadata.json').relative_to(ROOT).as_posix(),
                             checkpoint=checkpoint.relative_to(ROOT).as_posix()))
    files = {}
    for path in sorted(paths):
        if not path.is_file():
            raise FileNotFoundError(path)
        files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    output = ROOT / 'reports/audits/TV4_Run_Assets.json'
    output.write_text(json.dumps(dict(format_version=1, files=files, runs=runs), indent=2), encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
