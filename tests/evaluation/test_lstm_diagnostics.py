import numpy as np
import pandas as pd
import pytest
from backend.error_analysis.lstm_diagnostics import history_controls,describe,summarize_errors


def fixture():
    return pd.DataFrame(dict(cohort='synthetic',representation='fixture',method='lstm',seed=42,forecast_length=1,
        sample_id=['a','b','c'],forecast_origin=['2023-01-02','2023-01-03','2023-01-04'],
        target_date=['2023-01-03','2023-01-04','2023-01-05'],horizon_step=1,
        actual_price=[101.,98.,103.],predicted_price=[100.,100.,100.],origin_price=100.))


def test_controls_keep_origin_and_prefix_values_and_determinism():
    x=np.arange(101.,161.).reshape(2,30,1);copy=x.copy()
    controls=history_controls(x)
    np.testing.assert_array_equal(x,copy)
    for name,p in controls.items():
        np.testing.assert_array_equal(p[:,-1],x[:,-1])
        if name in ('reverse_prefix','shuffle_prefix'):
            np.testing.assert_array_equal(np.sort(p[:,:-1,0],axis=1),np.sort(x[:,:-1,0],axis=1))
    np.testing.assert_array_equal(controls['flat'],np.repeat(x[:,-1:],30,axis=1))
    np.testing.assert_array_equal(controls['shuffle_prefix'],history_controls(x)['shuffle_prefix'])


def test_hand_scoring_and_stress_partition():
    f=fixture();s=describe(f)
    assert s['mae_usd']==2 and s['rmse_usd']==pytest.approx(np.sqrt(14/3))
    assert s['mse_skill_vs_persistence']==0 and s['std_adjustment_usd']==0
    out=summarize_errors(f,{1:.025},window=2,top_n=1)
    assert out['stress'].error_count.sum()==3
    assert out['largest'].sample_id.tolist()==['c']
    assert len(out['rolling'])==2
    assert out['rolling'].mae_usd.tolist()==[1.5,2.5]


def test_duplicate_keys_fail():
    f=fixture()
    with pytest.raises(ValueError):describe(pd.concat([f,f]))


def test_h5_repeated_target_dates_are_distinguished_by_sample_and_step():
    f=pd.concat([fixture().assign(horizon_step=k,forecast_length=5) for k in range(1,6)])
    out=summarize_errors(f,{k:.025 for k in range(1,6)},window=2,top_n=1)
    overall=out['summary'][out['summary'].metric_scope=='overall'].iloc[0]
    assert overall.samples==3 and overall.error_count==15
    assert len(out['rolling'])==10
