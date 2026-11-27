import numpy as np
import pandas as pd
import pytest
from backend.error_analysis.validation_monitoring import analyze_validation_errors


def fixture():
    return pd.DataFrame(dict(method=['CNN']*21,seed=[42]*21,sample_id=list(map(str,range(21))),
        target_date=pd.bdate_range('2023-01-02',periods=21).strftime('%Y-%m-%d'),
        actual_usd=[100.]*21,predicted_usd=np.arange(1,22)+100.,error_usd=np.arange(1,22,dtype=float)))


def test_rolling_uses_only_last_twenty_and_preserves_input():
    data=fixture();before=data.copy(deep=True)
    result=analyze_validation_errors(data)
    assert result['rolling'].rolling_mae_usd.iloc[:19].isna().all()
    assert result['rolling'].rolling_mae_usd.iloc[19]==10.5
    assert result['rolling'].rolling_mae_usd.iloc[20]==11.5
    assert result['largest'].abs_error_usd.iloc[0]==21
    assert result['summary'].bias_usd.iloc[0]==11
    pd.testing.assert_frame_equal(data,before)


@pytest.mark.parametrize('damage',['residual','date','missing_target','actual'])
def test_inconsistent_rows_rejected(damage):
    a=fixture();b=a.copy();b['method']='LSTM'
    if damage=='residual': b.loc[0,'error_usd']=999
    if damage=='date': b=b.iloc[::-1]
    if damage=='missing_target': b=b.iloc[1:]
    if damage=='actual': b.loc[0,'actual_usd']=99;b.loc[0,'error_usd']+=1
    with pytest.raises(ValueError): analyze_validation_errors(pd.concat([a,b],ignore_index=True))
