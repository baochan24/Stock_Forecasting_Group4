"""Package existing TV1 artifacts locally, without downloading or publishing."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def sha256(content):
    return hashlib.sha256(content).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-version', required=True)
    parser.add_argument('--complete', action='store_true', help='Require raw, validated, metadata and validation report.')
    args = parser.parse_args()
    version = args.dataset_version
    if not version or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in version):
        raise ValueError('Dataset version must contain only letters, numbers, underscore or dash.')
    receipt_path = ROOT / f"data/metadata/aapl_handoff_{version}{'_complete' if args.complete else ''}.json"
    if receipt_path.exists():
        raise FileExistsError(f'Handoff already recorded: {receipt_path}; preserve the existing package.')
    meta_path = ROOT / f'data/metadata/aapl_metadata_{version}.json'
    raw_path = ROOT / f'data/raw/aapl_raw_{version}.csv'
    metadata = json.loads(meta_path.read_text(encoding='utf-8'))
    if metadata['dataset_version'] != version or metadata['ticker'] != 'AAPL' or metadata['currency'] != 'USD':
        raise ValueError('Metadata identity mismatch')
    if sha256(raw_path.read_bytes()) != metadata['raw_sha256']:
        raise ValueError('Raw snapshot hash mismatch')
    if (ROOT / metadata['raw_file']).resolve() != raw_path.resolve():
        raise ValueError('Raw path mismatch')
    files = [raw_path, meta_path]
    optional = [ROOT / f'data/validated/aapl_validated_{version}.csv', ROOT / f'data/metadata/aapl_validation_report_{version}.json']
    missing = [p.relative_to(ROOT).as_posix() for p in optional if not p.exists()]
    if args.complete:
        if missing:
            raise FileNotFoundError(f'Missing handoff artifacts: {missing}')
        report = json.loads(optional[1].read_text(encoding='utf-8'))
        if not report.get('passed') or report.get('dataset_version') != version:
            raise ValueError('Validation report failed or has the wrong version')
        for key, path in [('validated_sha256', optional[0]), ('raw_sha256', raw_path), ('source_metadata_sha256', meta_path)]:
            if report.get(key) != sha256(path.read_bytes()):
                raise ValueError(f'Validation provenance hash mismatch: {key}')
        files += optional + [ROOT / 'scripts/verify_tv1_handoff.py']
    # Full validated handoff requires a separate acceptance step; do not imply it here.
    manifest = {'dataset_version':version, 'created_at_utc':datetime.now(timezone.utc).isoformat(), 'status':'raw_snapshot_only', 'validated_handoff_complete':False, 'shared_location':None, 'recipient_verified':False, 'missing_validation_artifacts':missing, 'files':[{'path':p.relative_to(ROOT).as_posix(), 'sha256':sha256(p.read_bytes()), 'bytes':p.stat().st_size} for p in files]}
    if args.complete:
        manifest.update(status='complete_artifact_set', validated_handoff_complete=True,
                        recipient_verified=False, validation_scope='Existing validator plus package consistency; full quality audit tracked separately.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive = ROOT / f"artifacts/releases/{version}_{'complete' if args.complete else 'raw'}_handoff_{stamp}.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    instructions = 'TV1 RAW SNAPSHOT HANDOFF\nExtract into the project root; preserve data/raw and data/metadata paths.\nVerify ZIP SHA-256 against its .sha256 file before extraction.\nVerify each file SHA-256 against manifest.json after extraction.\nDo not replace existing files unless their hashes match.\nThis is a raw-only package, not a validated dataset or model release.\nDo not fit scalers/train until validation is accepted.\n'
    if args.complete:
        instructions = ('TV1 DATASET HANDOFF: raw + validated + source metadata + validation report.\n'
                        'Not a model/scaler release; no training is required to verify the package.\n'
                        'Download this ZIP and the matching .zip.sha256 file from Project_CW Drive.\n'
                        'Before extraction run: python scripts/verify_tv1_handoff.py --archive <zip> --checksum <zip.sha256>\n'
                        'The verifier uses only the Python standard library. Get it from this project source.\n'
                        'Extract into a NEW project copy; keep data/raw and data/metadata and data/validated paths.\n'
                        'Never overwrite existing files with different hashes.\n'
                        'Do not redownload Yahoo to reproduce this snapshot: adjusted prices may change.\n'
                        'Recipient should report dataset_version, ZIP SHA256 and verification output.\n'
                        'Independent recipient confirmation is still pending. Full data-quality audit is a separate task.\n')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
        for p in files:
            bundle.write(p, p.relative_to(ROOT).as_posix())
        bundle.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        bundle.writestr('HANDOFF.txt', instructions)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('Archive CRC verification failed')
        for item in manifest['files']:
            if sha256(bundle.read(item['path'])) != item['sha256']:
                raise ValueError('Packaged file hash mismatch')
    digest = sha256(archive.read_bytes())
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n', encoding='utf-8')
    receipt = {'archive':archive.relative_to(ROOT).as_posix(), 'archive_sha256':digest, 'archive_verified':True, **manifest}
    with receipt_path.open('x', encoding='utf-8') as output:
        json.dump(receipt, output, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=True, indent=2))

if __name__ == '__main__':
    main()
