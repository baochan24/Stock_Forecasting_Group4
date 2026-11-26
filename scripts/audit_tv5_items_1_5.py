"""Read-only TV5 acceptance audit, synthetic tests and real-data forward only."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from backend.experiments.runner.experiment_runner import load_experiment_config
    from backend.experiments.runner.cnn_factories import comparison_reference
    import nbformat
    import torch
    folder = ROOT / 'logs/audit' / ('tv5_audit_1_5_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True)
    paths = sorted({*ROOT.glob('backend/**/*.py'), *ROOT.glob('tests/models/test_cnn*.py'),
                    *ROOT.glob('tests/training/*.py'), ROOT / 'experiments/configs/cnn_one_step_baseline.yaml'})
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    intake = json.loads((ROOT / 'logs/audit/tv5_item1_20261126T030327572216Z/intake.json').read_text())
    protected = [name for name, sha in intake['protected_hashes'].items() if digest(ROOT / name) != sha]
    allowed = json.loads((ROOT / 'reports/audits/TV5_Item5_Source_Changes.json').read_text())
    allowed6 = ROOT / 'reports/audits/TV5_Item6_Source_Changes.json'
    if allowed6.is_file():
        allowed.update(json.loads(allowed6.read_text()))
    assert protected == ['backend/experiments/runner/experiment_runner.py']
    assert all(digest(ROOT / name) == allowed[name] for name in protected)
    changed_intake = [r['path'] for r in intake['files'] if digest(ROOT / r['path']) != r['sha256']]
    assert set(changed_intake) == {'backend/models/cnn_one_step/model.py', 'tests/models/test_cnn_one_step.py'}
    c = load_experiment_config(ROOT / 'experiments/configs/cnn_one_step_baseline.yaml')
    reference = load_experiment_config(ROOT / 'logs/audit/tv4_item7_20261125T120957429763Z/one_step_lb30.yaml')
    assert c['data'] == reference['data']
    assert c['seeds'] == [42,123,456]
    assert c['training'] == reference['training']
    assert c['model'] == dict(lookback=30,n_features=1,conv1_channels=16,conv2_channels=32,
                             kernel_size=3,pool_size=2,hidden_units=32,dropout=.1,output_size=1)
    # The generic validator deliberately validates supported values, not the experiment budget lock.
    probes = []
    for section, field, value in [('training','max_epochs',101), ('model','conv1_channels',32)]:
        alternative = deepcopy(c)
        alternative[section][field] = value
        comparison_reference(alternative)
        probes.append(dict(section=section,field=field,value=value,accepted_by_generic_validator=True))
    nb = nbformat.read(ROOT / 'notebooks/05_TV5_CNN_Development_and_Experiments.ipynb',as_version=4)
    cells = [cell for cell in nb.cells if cell.cell_type == 'code']
    assert all(cell.execution_count is not None for cell in cells)
    assert not any(o.output_type == 'error' for cell in cells for o in cell.outputs)
    env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONIOENCODING='utf-8')
    command = [sys.executable,'-m','pytest','tests/models/test_cnn_one_step.py',
               'tests/models/test_cnn_contract.py','tests/models/test_cnn_learning.py','tests/training',
               '-q','-p','no:cacheprovider','--junitxml=' + str(folder / 'tests.xml')]
    run = subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    (folder / 'pytest.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
    assert run.returncode == 0, run.stdout+run.stderr
    cases = list(ET.parse(folder / 'tests.xml').getroot().iter('testcase'))
    assert len(cases) >= 111
    assert not any(child.tag in ('failure','error','skipped') for case in cases for child in case)
    data_run = subprocess.run([sys.executable,'-X','utf8',str(ROOT / 'scripts/check_tv5_aapl_data.py')],
                              cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    assert data_run.returncode == 0, data_run.stdout+data_run.stderr
    data_path = Path(json.loads(data_run.stdout)['evidence'])
    data = json.loads(data_path.read_text())
    assert data['passed'] and not data['trained']
    assert all(digest(ROOT / name) == sha for name,sha in before.items())
    summary = dict(passed=True,tests=len(cases),aapl_training=False,test_performance_evaluated=False,
        data_evidence=data_path.relative_to(ROOT).as_posix(),data_results=data['results'],
        source_hashes=before,protected_changes=protected,intake_source_changes=changed_intake,
        source_unchanged_during_audit=True,notebook_executed_cells=len(cells),
        config_matches_lstm_data=True,generic_config_probes=probes,
        python=sys.version,torch=torch.__version__,command=command,
        limitations=['Generic config validation does not lock Option A architecture/budget',
                     'Data audit requires local historical TV4 evidence',
                     'No AAPL training or final checkpoint acceptance in items 1-5'])
    (folder / 'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,evidence=str(folder / 'summary.json'))))


if __name__ == '__main__':
    main()
