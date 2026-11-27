"""Enforce the frozen semantic configuration for official CNN Option A runs."""
from backend.artifacts.cnn_checkpoint import fingerprint

FIELDS = ('model_type','data','model','training','seeds','runtime')


def validate_official_plan(config, plan):
    semantic = {key:config[key] for key in FIELDS}
    if plan.get('format_version') != 1 or plan.get('purpose') != 'research':
        raise ValueError('Invalid CNN research plan')
    if fingerprint(plan['semantic_config']) != plan.get('semantic_sha256'):
        raise ValueError('CNN plan fingerprint mismatch')
    if semantic != plan['semantic_config']:
        raise ValueError('CNN official configuration differs from locked Option A')
    return plan['semantic_sha256']
