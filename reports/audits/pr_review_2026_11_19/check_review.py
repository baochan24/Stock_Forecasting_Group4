from pathlib import Path
import importlib.util
import sys
import unittest
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

source = (ROOT / 'pr2/backend/data/preparation/README.md').read_text(encoding='utf-8')
try:
    compile(source, 'PR2', 'exec')
except SyntaxError as exc:
    print('PR2 syntax:', type(exc).__name__, exc.lineno, exc.msg)

validator = load('validator', ROOT / 'pr5/backend/data/validation/validator.py')
for name, dates in [
    ('only_three_sessions', ['2015-01-02', '2015-01-05', '2015-01-06']),
    ('weekend_session', ['2015-01-03', '2015-01-05']),
    ('missing_middle_session', ['2015-01-02', '2015-01-06']),
]:
    report, _ = validator.inspect_raw_dataframe(pd.DataFrame({'date': dates, 'Adj Close': [25.] * len(dates)}), 'audit')
    print(name, 'passed=', report['passed'], 'counts=', report.get('split_session_counts'))

# Diagnostic only: repair indentation in memory to inspect the next integration issue.
namespace = {}
exec(source.replace('\ninput_scaled =', '\n        input_scaled ='), namespace)
dates = pd.bdate_range('2022-11-01', '2024-02-29')
prices = np.arange(1, len(dates) + 1, dtype=np.float32).reshape(-1, 1)
scaler = namespace['fit_scaler'](prices[dates.year == 2022])
for horizon in [1, 5]:
    mask = dates.year == 2023
    result = namespace['create_windows'](dates[mask].strftime('%Y-%m-%d').tolist(), prices[mask], scaler, forecast_length=horizon, split_name='val')
    print('PR2 after in-memory syntax repair:', 'horizon=', horizon, 'val_sessions=', int(mask.sum()), 'samples=', result['num_samples'], 'first_target=', result['samples'][0]['target_dates'][0], 'expected_with_prior_context=', int(mask.sum()) - horizon + 1)

sys.modules['backend.data.validation.validator'] = validator
suite_module = load('pr5_tests', ROOT / 'pr5/tests/data/test_data_pipeline.py')
suite = unittest.defaultTestLoader.loadTestsFromModule(suite_module)
unittest.TextTestRunner(verbosity=2).run(suite)
