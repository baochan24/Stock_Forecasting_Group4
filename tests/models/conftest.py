"""Synthetic TV2 module fixture; actual artifacts are checked by the CLI."""
import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler


@pytest.fixture
def tv2_source():
    dates = (pd.bdate_range("2022-10-03",periods=40).strftime("%Y-%m-%d").tolist()
             + pd.bdate_range("2023-12-01",periods=10).strftime("%Y-%m-%d").tolist()
             + pd.bdate_range("2024-01-02",periods=10).strftime("%Y-%m-%d").tolist())
    data = pd.DataFrame({"date":dates,"ticker":"AAPL","adjusted_close":np.arange(1.,61.),"dataset_version":"fixture"})
    return data,StandardScaler().fit(np.arange(1.,41.).reshape(-1,1))
