"""Verify an extracted TV4 payload, then reload its twelve research checkpoints."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'TV4_HANDOFF.json').read_text(encoding='utf-8'))
    for name, digest in manifest['files'].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError(f'Unsafe payload member: {name}')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Payload checksum mismatch: {name}')
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/verify_tv4_assets.py'),
                    '--root', str(ROOT), '--models'], cwd=ROOT, check=True)
    print(json.dumps(dict(passed=True, payload_files=len(manifest['files']),
                          research_models=12, selected_models=len(manifest['selected_models']),
                          recipient_machine_verified=False)))


if __name__ == '__main__':
    main()
