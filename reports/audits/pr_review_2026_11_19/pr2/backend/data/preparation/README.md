
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def split_data(validated_file_path: str) -> dict:
    """
    Chia dữ liệu theo thời gian:
    Train: 2015-2022
    Validation: 2023
    Test: 2024-2025
    """

    df = pd.read_csv(validated_file_path)

    required_columns = ["date", "ticker", "adjusted_close"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if df["date"].duplicated().any():
        raise ValueError("Duplicate dates found in dataset.")

    if df["adjusted_close"].isna().any():
        raise ValueError("Missing adjusted_close values.")

    if (df["adjusted_close"] <= 0).any():
        raise ValueError("Prices must be positive.")

    train = df[df["date"].dt.year.between(2015, 2022)]
    val = df[df["date"].dt.year == 2023]
    test = df[df["date"].dt.year.between(2024, 2025)]

    def convert_data(data):
        return {
            "dates": data["date"].dt.strftime(
                "%Y-%m-%d"
            ).tolist(),
            "prices": data["adjusted_close"].to_numpy(
                dtype=np.float32
            ).reshape(-1, 1)
        }

    if train.empty or val.empty or test.empty:
        raise ValueError("One or more dataset splits are empty.")

    return {
        "train": convert_data(train),
        "val": convert_data(val),
        "test": convert_data(test)
    }


def fit_scaler(train_prices: np.ndarray) -> StandardScaler:
    """
    Fit StandardScaler trên tập train.
    Chỉ được gọi một lần.
    """

    train_prices = np.asarray(
        train_prices, dtype=np.float32
    ).reshape(-1, 1)

    scaler = StandardScaler()
    scaler.fit(train_prices)

    return scaler


def create_windows(
    dates,
    prices,
    scaler,
    lookback=30,
    forecast_length=1,
    split_name="train"
):
    """
    Tạo cửa sổ dữ liệu đầu vào và mục tiêu dự báo.

    Input: 30 phiên trước đó.
    Target: 1 hoặc 5 phiên tiếp theo.
    """

    if lookback <= 0:
        raise ValueError("lookback must be positive.")

    if forecast_length not in (1, 5):
        raise ValueError("forecast_length must be 1 or 5.")

    prices = np.asarray(
        prices, dtype=np.float32
    ).reshape(-1, 1)

    if len(dates) != len(prices):
        raise ValueError("Dates and prices must have equal length.")

    if len(prices) < lookback + forecast_length:
        raise ValueError("Not enough data to create windows.")

    scaled_prices = scaler.transform(prices)

    samples = []

    for i in range(len(prices) - lookback - forecast_length + 1):

        input_start = i
        input_end = i + lookback

        target_end = input_end + forecast_length

        input_values = prices[input_start:input_end]
        target_values = prices[input_end:target_end]
input_scaled = scaled_prices[input_start:input_end]
        target_scaled = scaled_prices[input_end:target_end]

        sample = {
            "sample_id": f"{split_name}_{i:06d}",

            "forecast_origin": dates[input_end - 1],

            "input_dates": dates[input_start:input_end],

            "input_values": input_values.copy(),

            "input_scaled": input_scaled.copy(),

            "target_dates": dates[input_end:target_end],

            "target_values": target_values.flatten().copy(),

            "target_scaled": target_scaled.flatten().copy(),

            "split": split_name
        }

        samples.append(sample)

    return {
        "samples": samples,
        "num_samples": len(samples),
        "lookback": lookback,
        "forecast_length": forecast_length
    }

