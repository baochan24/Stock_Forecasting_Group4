"""Create a local, checksummed TV4 source and trained-model handoff."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile
import argparse
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage-dir', type=Path)
    args = parser.parse_args()
    inventory_path = ROOT / 'reports/audits/TV4_Run_Assets.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    names = set(inventory['files'])
    for pattern in ('tests/**/*.py', 'tests/**/*.json', 'docs/*.md', 'reports/**/*.md',
                    'reports/audits/TV4*.json', 'notebooks/04_TV4*.ipynb',
                    'experiments/configs/*.yaml'):
        names.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern) if p.is_file())
    names.update(['rule.md', 'README.md', 'FILE_STRUCTURE.md', 'reports/audits/TV4_Run_Assets.json'])
    latest = ROOT / 'logs/audit/tv4_item10_latest.json'
    if latest.is_file():
        names.add(latest.relative_to(ROOT).as_posix())
    source = ROOT / 'logs/audit/tv4_item7_20261125T120957429763Z'
    names.update(p.relative_to(ROOT).as_posix() for p in source.glob('*.yaml'))
    hashes = {}
    for name in sorted(names):
        path = ROOT / name
        if '__pycache__' in path.parts:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if name in inventory['files'] and digest != inventory['files'][name]:
            raise ValueError(f'Inventory changed: {name}')
        hashes[name] = digest
    selected = []
    for entry in inventory['runs']:
        meta = json.loads((ROOT / entry['metadata']).read_text(encoding='utf-8'))
        if meta['config']['data']['lookback'] == 30:
            selected.append(entry)
    assert len(selected) == 6
    handoff = dict(format_version=1, selected_models=selected, total_research_runs=12,
                   recipient_machine_verified=False, scope='TV4 training handoff, validation-selected', files=hashes)
    if args.stage_dir:
        stage = args.stage_dir.resolve()
        stage.mkdir(parents=True, exist_ok=False)
        for name in hashes:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        (stage / 'TV4_HANDOFF.json').write_text(json.dumps(handoff, indent=2), encoding='utf-8')
        print(json.dumps(dict(stage=str(stage), files=len(hashes))))
        return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / 'artifacts/releases' / f'TV4_Handoff_{stamp}.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in hashes:
            archive.write(ROOT / name, name)
        archive.writestr('TV4_HANDOFF.json', json.dumps(handoff, indent=2))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(f'{digest}  {output.name}\n', encoding='utf-8')
    print(json.dumps(dict(zip=str(output), sha256=digest, files=len(hashes), selected_models=6)))


if __name__ == '__main__':
    main()
