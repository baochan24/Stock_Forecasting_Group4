"""Freeze the evaluation contract before test inference; never load model weights."""
import hashlib
import json
from pathlib import Path
import csv
import re

PROTOCOL_PATH='experiments/configs/tv6_evaluation_protocol_v1.json'
REGISTRY_PATH='experiments/configs/tv6_evaluation_protocol_v1.registry.json'


def resolve_member(root,name):
    root=Path(root).resolve()
    if (not isinstance(name,str) or not name or '\\' in name or ':' in name
            or Path(name).is_absolute() or '..' in Path(name).parts):
        raise ValueError('Unsafe artifact path')
    result=(root/name).resolve()
    if not result.is_relative_to(root): raise ValueError('Artifact outside accepted root')
    return result


def tracked_member(root,files,name):
    if name not in files: raise ValueError('Reference is not pinned in intake: '+str(name))
    return resolve_member(root,name)


def verify_model_reference(root,inventory,model):
    files=inventory['files']
    folder=resolve_member(root,model['checkpoint'])
    manifest_path=tracked_member(root,files,model['checkpoint']+'/manifest.json')
    tracked_member(root,files,model['checkpoint']+'/weights.pt')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    meta=manifest['metadata'];config=meta['training_config'];data=config['data']
    for key in ('run_id','seed','best_epoch','prepared_id','scaler_id'):
        if meta.get(key)!=model[key]: raise ValueError('Model reference/manifest mismatch: '+key)
    if (manifest.get('checkpoint_id')!=folder.name or meta.get('trained') is not True
            or meta.get('selected_on')!='validation' or meta.get('purpose')=='diagnostic'
            or meta.get('dataset_version')!=inventory['dataset_version']
            or meta.get('source_hashes')!=inventory['source_hashes']):
        raise ValueError('Checkpoint identity/purpose/provenance mismatch')
    wanted='cnn_one_step' if model['method']=='CNN' else 'lstm_one_step' if model['forecast_length']==1 else 'lstm_multi_step'
    if (config.get('model_type')!=wanted or data.get('lookback')!=30
            or data.get('forecast_length')!=model['forecast_length']
            or data.get('prepared_id')!=model['prepared_id'] or data.get('scaler_id')!=model['scaler_id']
            or data.get('dataset_version')!=inventory['dataset_version']):
        raise ValueError('Checkpoint mode/config mismatch')
    for relative in (f"data/prepared/{model['prepared_id']}/manifest.json",
                     f"artifacts/scalers/{model['scaler_id']}/manifest.json"):
        tracked_member(root,files,relative)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def build_protocol(root):
    root=Path(root).resolve()
    inventory_path=root/'reports/audits/TV6_Input_Inventory.json'
    inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('passed') is not True or inventory.get('test_performance_evaluated') is not False:
        raise ValueError('Intake must be accepted and not test-evaluated')
    if not isinstance(inventory.get('files'),dict) or not inventory['files']:
        raise ValueError('Empty intake file inventory')
    for name,expected in inventory['files'].items():
        path=resolve_member(root,name)
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):
            raise ValueError('Invalid artifact digest')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Intake artifact changed: '+name)
    models=[{k:m[k] for k in ('method','forecast_length','lookback','seed','run_id','best_epoch',
                             'checkpoint','prepared_id','scaler_id')} for m in inventory['models']]
    expected_groups={('LSTM',1),('LSTM',5),('CNN',1)}
    if len(models)!=9 or {(m['method'],m['forecast_length']) for m in models}!=expected_groups:
        raise ValueError('Expected exactly three accepted model groups')
    for method,h in expected_groups:
        if sorted(m['seed'] for m in models if (m['method'],m['forecast_length'])==(method,h))!=[42,123,456]:
            raise ValueError('Expected all three predefined seeds per model group')
    if len({m['checkpoint'] for m in models})!=9 or len({m['run_id'] for m in models})!=9:
        raise ValueError('Duplicate checkpoint/run references')
    scaler_ids={m['scaler_id'] for m in models}
    if len(scaler_ids)!=1: raise ValueError('Different scalers across accepted models')
    for model in models:
        if (type(model['seed']) is not int or type(model['forecast_length']) is not int
                or type(model['lookback']) is not int or model['lookback']!=30
                or type(model['best_epoch']) is not int or model['best_epoch']<1):
            raise ValueError('Invalid model seed/horizon/lookback/epoch types')
        verify_model_reference(root,inventory,model)
    source_path=tracked_member(root,inventory['files'],f"data/validated/aapl_validated_{inventory['dataset_version']}.csv")
    with source_path.open(encoding='utf-8-sig',newline='') as stream:
        dates=[r['date'] for r in csv.DictReader(stream)]
    if dates!=sorted(set(dates)):raise ValueError('Source dates must be unique and ordered')
    cohorts=[]
    for h in (1,5):
        prepared_ids={m['prepared_id'] for m in models if m['forecast_length']==h}
        if len(prepared_ids)!=1: raise ValueError('Different prepared inputs within comparison')
        prepared_id=prepared_ids.pop()
        base=f'data/prepared/{prepared_id}/'
        inputs=json.loads(tracked_member(root,inventory['files'],base+f'f{h}_test_inputs.json').read_text())
        targets=json.loads(tracked_member(root,inventory['files'],base+f'f{h}_test_targets.json').read_text())
        tracked_member(root,inventory['files'],base+f'f{h}_test.npz')
        if len(inputs)!=len(targets) or not inputs: raise ValueError('Incomplete cohort')
        keys=[]
        for x,y in zip(inputs,targets):
            if x['sample_id']!=y['sample_id'] or y['split']!='test' or len(y['target_dates'])!=h:
                raise ValueError('Wrong cohort pairing/split/horizon')
            if (x.get('dataset_version')!=inventory['dataset_version']
                    or type(x.get('lookback')) is not int or x['lookback']!=30
                    or type(x.get('forecast_length')) is not int or x['forecast_length']!=h
                    or x['sample_id']!=f"{inventory['dataset_version']}:lb30:f{h}:{x['forecast_origin']}"
                    or y.get('horizon_step')!=list(range(1,h+1))):
                raise ValueError('Cohort record identity/mode mismatch')
            if not all('2024-01-01'<=d<='2025-12-31' and d>x['forecast_origin'] for d in y['target_dates']):
                raise ValueError('Targets outside frozen test or before origin')
            keys.append(dict(sample_id=x['sample_id'],forecast_origin=x['forecast_origin'],target_dates=y['target_dates']))
        expected_indices=[i for i,d in enumerate(dates) if i>=30 and '2024-01-01'<=d<='2025-12-31'
            and i+h<=len(dates) and all('2024-01-01'<=v<='2025-12-31' for v in dates[i:i+h])]
        if len(keys)!=len(expected_indices):raise ValueError('Incomplete eligible test coverage')
        for x,key,i in zip(inputs,keys,expected_indices):
            if (key['forecast_origin']!=dates[i-1] or key['target_dates']!=dates[i:i+h]
                    or x['input_dates']!=dates[i-30:i]):
                raise ValueError('Cohort dates/order/history differ from accepted source')
        if len({k['sample_id'] for k in keys})!=len(keys): raise ValueError('Duplicate cohort sample IDs')
        cohorts.append(dict(forecast_length=h,prepared_id=prepared_id,samples=len(keys),
            ordered_keys_sha256=digest(keys),first_origin=keys[0]['forecast_origin'],
            first_target=keys[0]['target_dates'][0],last_target=keys[-1]['target_dates'][-1],
            methods=['LSTM','CNN','persistence'] if h==1 else ['LSTM','persistence'],
            evaluation_style='rolling observed history; frozen weights/scaler; direct multi-output for h5'))
    semantic=dict(protocol_id='tv6-final-evaluation-v1',dataset_version=inventory['dataset_version'],
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        artifacts_sha256=inventory['files'],models=models,cohorts=cohorts,
        metrics=dict(primary=['MAE_USD','RMSE_USD'],currency='USD',round_before_metric=False,
            per_horizon=True,multi_step_secondary_overall='flatten all sample-horizon errors; sqrt of mean squared errors',
            seed_summary='mean of per-seed metrics and sample std ddof1; no ensemble',std_ddof=1,
            pooling_seed_predictions=False,compare_only_identical_ordered_keys=True,
            float64_numeric_tie_atol_usd=1e-12,practical_significance_threshold=None,
            significance_claim=False,baseline='last observed raw USD input, repeat for h5'),
        demo=dict(seed=42,rule='fixed seed42 for all neural methods/modes, chosen before test',
            run_ids=[m['run_id'] for m in models if m['seed']==42],
            default_method_policy='show supported methods; no automatic test winner selection'),
        runtime=dict(device='cpu',dtype='float64',torch_threads=1,inference_batch_size=32,
            drop_last=False,shuffle=False),
        evaluation_policy=dict(no_retraining=True,no_refit_scaler=True,no_test_tuning=True,
            no_seed_selection_on_test=True,checkpoint_selection='already accepted validation best epoch',
            missing_or_misaligned_samples='fail comparison; no silent intersection/drop',
            changed_artifact='invalidate protocol and require explicit version change',
            tie_interpretation='numeric equality only, not practical or statistical equivalence',
            mixed_mae_rmse='report tradeoff, no composite score',
            rolling_error_window_sessions=20,largest_errors_per_run=10,
            scope='full frozen test primary; subsets clearly labelled exploratory'),
        limitations=['Daily adjusted-close retrospectively adjusted snapshot, not point-in-time market replay',
            'Overlapping h5 windows are dependent; no naive independent-sample significance claims',
            'LSTM lookback search and fixed CNN architecture have unequal search budgets',
            'Frozen historical rolling evaluation, not continuous/live deployment'])
    return dict(format_version=1,semantic=semantic,semantic_sha256=digest(semantic),
                test_performance_evaluated_at_lock=False)


def validate_protocol(protocol,root,*,require_registry=True):
    if not isinstance(protocol,dict) or type(protocol.get('format_version')) is not int or protocol['format_version']!=1 or protocol.get('test_performance_evaluated_at_lock') is not False:
        raise ValueError('Invalid protocol format or test exposure status')
    if not isinstance(protocol.get('semantic'),dict) or not isinstance(protocol.get('semantic_sha256'),str):
        raise ValueError('Invalid protocol schema')
    if digest(protocol['semantic'])!=protocol.get('semantic_sha256'):
        raise ValueError('Protocol fingerprint mismatch')
    current=build_protocol(root)
    if protocol!=current:
        raise ValueError('Protocol differs from accepted artifacts or fixed evaluation policy')
    if require_registry:
        registry_path=Path(root)/REGISTRY_PATH
        if not registry_path.is_file():raise ValueError('Missing protocol registry; explicit registration required')
        registry=json.loads(registry_path.read_text(encoding='utf-8'))
        path=Path(root)/PROTOCOL_PATH
        if (not isinstance(registry,dict) or type(registry.get('format_version')) is not int or registry['format_version']!=1
                or registry.get('protocol_id')!=protocol['semantic']['protocol_id']
                or registry.get('semantic_sha256')!=protocol['semantic_sha256']
                or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=registry.get('protocol_file_sha256')):
            raise ValueError('Protocol differs from registered immutable lock')
        prior=registry.get('prior_receipt')
        if prior is not None:
            evidence=resolve_member(root,prior['path'])
            if not evidence.is_file() or hashlib.sha256(evidence.read_bytes()).hexdigest()!=prior.get('sha256'):
                raise ValueError('Registered prior receipt differs or is missing')
    return protocol['semantic_sha256']
