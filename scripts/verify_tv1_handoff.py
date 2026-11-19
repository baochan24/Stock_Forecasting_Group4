"""Verify a complete TV1 archive without extraction or third-party dependencies."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import zipfile


def verify(archive, checksum):
    archive = Path(archive)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    expected = Path(checksum).read_text(encoding='utf-8').split()[0]
    if actual != expected:
        raise ValueError('ZIP checksum mismatch')
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or bundle.testzip() is not None:
            raise ValueError('Duplicate members or damaged ZIP')
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe archive path')
        manifest = json.loads(bundle.read('manifest.json'))
        version = manifest['dataset_version']
        if manifest.get('status') != 'complete_artifact_set':
            raise ValueError('Not a complete artifact set')
        paths = [item['path'] for item in manifest['files']]
        if len(paths) != len(set(paths)) or set(names) != set(paths) | {'manifest.json','HANDOFF.txt'}:
            raise ValueError('Manifest membership mismatch')
        hashes = {}
        for item in manifest['files']:
            data = bundle.read(item['path'])
            hashes[item['path']] = hashlib.sha256(data).hexdigest()
            if hashes[item['path']] != item['sha256'] or len(data) != item['bytes']:
                raise ValueError('Member hash/size mismatch: '+item['path'])
        raw_name = f'data/raw/aapl_raw_{version}.csv'
        meta_name = f'data/metadata/aapl_metadata_{version}.json'
        val_name = f'data/validated/aapl_validated_{version}.csv'
        report_name = f'data/metadata/aapl_validation_report_{version}.json'
        meta = json.loads(bundle.read(meta_name))
        report = json.loads(bundle.read(report_name))
        for field, path, document in [('raw_sha256',raw_name,meta), ('raw_sha256',raw_name,report), ('source_metadata_sha256',meta_name,report), ('validated_sha256',val_name,report)]:
            if document.get(field) != hashes[path]:
                raise ValueError('Artifact linkage mismatch: '+field)
        if meta.get('dataset_version') != version or report.get('dataset_version') != version or not report.get('passed') or not report.get('provenance',{}).get('passed'):
            raise ValueError('Wrong version or failed validation/provenance report')
        if meta.get('ticker') != 'AAPL' or meta.get('currency') != 'USD':
            raise ValueError('Wrong ticker/currency')
        raw_reader = csv.DictReader(io.StringIO(bundle.read(raw_name).decode('utf-8')))
        val_reader = csv.DictReader(io.StringIO(bundle.read(val_name).decode('utf-8')))
        if raw_reader.fieldnames != meta.get('columns') or val_reader.fieldnames != ['date','ticker','adjusted_close','dataset_version']:
            raise ValueError('Schema mismatch')
        raw, val = list(raw_reader), list(val_reader)
        if not raw or len(raw) != len(val) or len(raw) != meta.get('row_count') or len(val) != report.get('row_count'):
            raise ValueError('Row count mismatch')
        for r, v in zip(raw, val):
            rp, vp = float(r['Adj Close']), float(v['adjusted_close'])
            if r['date'] != v['date'] or v['ticker'] != 'AAPL' or v['dataset_version'] != version or not math.isfinite(rp) or not math.isfinite(vp) or rp <= 0 or not math.isclose(rp,vp,rel_tol=1e-12,abs_tol=1e-12):
                raise ValueError('Raw/validated row mismatch')
    return {'passed':True, 'dataset_version':version, 'zip_sha256':actual, 'member_count':len(names), 'raw_rows':len(raw), 'validated_rows':len(val), 'raw_validated_aligned':True, 'recipient_verified':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True)
    parser.add_argument('--checksum',required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.archive,args.checksum),indent=2))
