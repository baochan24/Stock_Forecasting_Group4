"""Persisted execution context for the authorized frozen held-out evaluation."""
import json
from pathlib import Path


def validate_test_run(root, path, protocol_sha256):
    root = Path(root).resolve()
    path = Path(path).resolve()
    if path.parent.parent != root / 'logs' / 'audit' or not path.parent.name.startswith('tv6_item5_') or path.name != 'execution.json':
        raise ValueError('Test context must be an item5 execution ledger')
    receipt = json.loads(path.read_text(encoding='utf-8'))
    if (receipt.get('status') != 'running' or receipt.get('protocol_sha256') != protocol_sha256
            or receipt.get('authorization') != 'User requested TV6 item5'
            or receipt.get('run_id') != path.parent.name):
        raise ValueError('Inactive or mismatched test execution context')
    return receipt
