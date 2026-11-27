"""Create once or verify the TV6 final-evaluation lock. No test model inference."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import argparse
import hashlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.audit.tv6_protocol import build_protocol,validate_protocol,PROTOCOL_PATH,REGISTRY_PATH


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register-existing',action='store_true',help='Explicitly anchor an existing valid pre-test lock; never overwrite a registry')
    args=parser.parse_args()
    path=ROOT/PROTOCOL_PATH
    registry_path=ROOT/REGISTRY_PATH
    existed=path.exists()
    if registry_path.exists() and not existed:
        raise ValueError('Registered lock was removed; refusing silent recreation')
    if not existed and not registry_path.exists():
        for prior in (ROOT/'logs/audit').glob('tv6_item2_*/summary.json'):
            old=json.loads(prior.read_text(encoding='utf-8'))
            if old.get('passed') is True and old.get('protocol')==PROTOCOL_PATH:
                raise ValueError('Historical lock receipt exists; refusing silent recreation of missing lock/registry')
    if path.exists():
        protocol=json.loads(path.read_text(encoding='utf-8'))
    else:
        protocol=build_protocol(ROOT)
        with path.open('x',encoding='utf-8') as stream: json.dump(protocol,stream,indent=2)
    if not registry_path.exists():
        if existed and not args.register_existing:
            raise ValueError('Existing lock requires explicit --register-existing adoption')
        validate_protocol(protocol,ROOT,require_registry=False)
        basis=None
        if existed:
            for prior in sorted((ROOT/'logs/audit').glob('tv6_item2_*/summary.json')):
                old=json.loads(prior.read_text(encoding='utf-8'))
                if old.get('passed') is True and old.get('semantic_sha256')==protocol['semantic_sha256'] and old.get('test_performance_evaluated') is False:
                    basis=dict(path=prior.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(prior.read_bytes()).hexdigest())
                    break
            if basis is None:raise ValueError('No matching pre-existing protocol receipt for explicit adoption')
        registry=dict(format_version=1,protocol_id=protocol['semantic']['protocol_id'],
            semantic_sha256=protocol['semantic_sha256'],protocol_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            registered_at_utc=datetime.now(timezone.utc).isoformat(),prior_receipt=basis,
            purpose='local immutable lock anchor, not authentication or proof of external test non-exposure')
        with registry_path.open('x',encoding='utf-8') as stream:json.dump(registry,stream,indent=2)
    fingerprint=validate_protocol(protocol,ROOT)
    folder=ROOT/'logs/audit'/('tv6_item2_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    receipt=dict(passed=True,protocol=path.relative_to(ROOT).as_posix(),semantic_sha256=fingerprint,
        models=len(protocol['semantic']['models']),cohorts=protocol['semantic']['cohorts'],
        demo=protocol['semantic']['demo'],test_performance_evaluated=False,trained_again=False)
    (folder/'summary.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    (ROOT/'logs/audit/tv6_item2_latest.json').write_text(json.dumps(dict(evidence=(folder/'summary.json').relative_to(ROOT).as_posix()),indent=2))
    print(json.dumps(dict(passed=True,evidence=str(folder/'summary.json'),semantic_sha256=fingerprint)))


if __name__=='__main__':main()
