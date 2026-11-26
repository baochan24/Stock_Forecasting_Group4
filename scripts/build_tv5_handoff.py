"""Package TV5 plus explicit local data/model dependencies. No upload or Git write."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def payload():
    names=set()
    patterns=['backend/**/*.py','backend/**/README.md','tests/**/*.py','tests/**/*.json',
        'scripts/*.py','scripts/requirements*txt','docs/*.md','reports/**/*.md','reports/audits/TV5*.json',
        'experiments/configs/*.yaml','experiments/configs/cnn*.json','notebooks/0*.ipynb',
        'notebooks/requirements*txt','notebooks/README.md']
    for pattern in patterns:
        names.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern)
                     if p.is_file() and '__pycache__' not in p.parts and '_UPDATED' not in p.name)
    names.update(['rule.md','README.md','FILE_STRUCTURE.md'])
    inventory=json.loads((ROOT/'reports/audits/TV4_Run_Assets.json').read_text())
    names.update(n for n in inventory['files'] if n.startswith(('data/','artifacts/scalers/')))
    cnn_path=sorted((ROOT/'logs/audit').glob('tv5_item8_*/summary.json'))[-1]
    cnn=json.loads(cnn_path.read_text())
    selected=[row['checkpoint_path'] for row in cnn['results']]
    smoke_path=sorted((ROOT/'logs/audit').glob('tv5_item7_*/summary.json'))[-1]
    smoke=json.loads(smoke_path.read_text())
    keep_checkpoints=selected+[smoke['checkpoint_path']]
    for p in (ROOT/'logs/audit').glob('tv5*'):
        if 'tmp' in p.name or p.name=='tv5_item10_latest.json': continue
        files=p.rglob('*') if p.is_dir() else [p]
        for f in files:
            if not f.is_file() or '__pycache__' in f.parts: continue
            name=f.relative_to(ROOT).as_posix()
            if '/checkpoints/' in name and not any(name.startswith(k+'/') for k in keep_checkpoints): continue
            names.add(name)
    tv4=ROOT/'logs/audit/tv4_item8_20261125T122649342552Z'
    names.add((tv4/'summary.json').relative_to(ROOT).as_posix())
    for row in json.loads((tv4/'summary.json').read_text())['results']:
        if row['lookback']!=30: continue
        folder=ROOT/'artifacts/checkpoints/tv4_item8_20261125T122649342552Z'/Path(row['checkpoint']).name
        names.update(f.relative_to(ROOT).as_posix() for f in folder.glob('*') if f.is_file())
        names.update(f.relative_to(ROOT).as_posix() for f in (tv4/'runs'/row['run_id']).glob('*') if f.is_file())
    names.add('logs/audit/tv4_item7_20261125T120957429763Z/one_step_lb30.yaml')
    # Protected hashes include earlier notebooks, ensure those exact canonical files ship.
    intake=json.loads((ROOT/'logs/audit/tv5_item1_20261126T030327572216Z/intake.json').read_text())
    names.update(intake['protected_hashes'])
    return sorted(names),selected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage-dir',type=Path)
    args=parser.parse_args()
    names,selected=payload()
    hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
    assert all(not any(part in ('.git','.venv','__pycache__') for part in Path(n).parts) for n in names)
    manifest=dict(format_version=1,scope='TV5 items1-10, local validation handoff',files=hashes,
        cnn_checkpoints=selected,cnn_research_models=3,lstm_comparison_models=3,
        recipient_machine_verified=False,test_performance_evaluated=False,
        dependencies='Accepted TV1/TV2 artifacts and historical TV4 comparison evidence included')
    if args.stage_dir:
        stage=args.stage_dir.resolve()
        if not stage.is_relative_to(ROOT): raise ValueError('Stage must stay inside workspace')
        stage.mkdir(parents=True,exist_ok=False)
        for name in names:
            dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
        (stage/'TV5_HANDOFF.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(json.dumps(dict(stage=str(stage),files=len(names))))
        return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'artifacts/releases'/('TV5_Handoff_'+stamp+'.zip')
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names: archive.write(ROOT/name,name)
        archive.writestr('TV5_HANDOFF.json',json.dumps(manifest,indent=2))
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_suffix('.zip.sha256').write_text(digest+'  '+out.name+'\n',encoding='utf-8')
    print(json.dumps(dict(zip=str(out),sha256=digest,files=len(names))))


if __name__=='__main__':main()
