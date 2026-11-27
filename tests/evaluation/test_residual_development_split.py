import pytest
from scripts.run_tv6_residual_development import select_records


def test_all_targets_stay_in_fold_with_previous_history_allowed():
    inputs=[dict(sample_id=str(i),forecast_origin='2021-12-30') for i in range(3)]
    targets=[dict(sample_id='0',target_dates=['2021-12-31','2022-01-03']),
             dict(sample_id='1',target_dates=['2022-01-03','2022-01-04']),
             dict(sample_id='2',target_dates=['2022-12-30','2023-01-03'])]
    selected=select_records(inputs,targets,'2022-01-01','2022-12-31')
    assert [x['sample_id'] for x,y in selected]==['1']
    assert selected[0][0]['forecast_origin']=='2021-12-30'


def test_mismatched_pair_rejected():
    with pytest.raises(ValueError):select_records([{'sample_id':'x'}],[{'sample_id':'y','target_dates':['2022-01-03']}],'2022-01-01','2022-12-31')
