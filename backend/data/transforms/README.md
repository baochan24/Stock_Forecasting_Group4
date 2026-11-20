# data/transforms

Phép chuẩn hóa, inverse transform, tạo cửa sổ dùng chung. Không tự fit lại scaler.

Trạng thái: vị trí triển khai dự kiến; chưa có code hoặc kiểm chứng. Chưa chọn tên file implementation để tránh tạo stub chạy giả.

import numpy as np
from sklearn.preprocessing import StandardScaler


def scale(
    values: np.ndarray,
    scaler: StandardScaler
) -> np.ndarray:
    """
    Chuẩn hóa dữ liệu bằng StandardScaler.
    Không fit lại scaler.
    """

    values = np.asarray(values, dtype=np.float32)

    if values.size == 0:
        raise ValueError("Dữ liệu đầu vào không được rỗng.")

    original_shape = values.shape

    if values.ndim == 1:
        values_2d = values.reshape(-1, 1)
    elif values.ndim == 2:
        values_2d = values
    else:
        raise ValueError("Dữ liệu chỉ được có 1 hoặc 2 chiều.")

    scaled_values = scaler.transform(values_2d)

    return scaled_values.reshape(original_shape)


def inverse_scale(
    scaled_values: np.ndarray,
    scaler: StandardScaler
) -> np.ndarray:
    """
    Khôi phục dữ liệu về giá trị ban đầu.
    """

    scaled_values = np.asarray(
        scaled_values,
        dtype=np.float32
    )

    if scaled_values.size == 0:
        raise ValueError("Dữ liệu đầu vào không được rỗng.")

    original_shape = scaled_values.shape

    if scaled_values.ndim == 1:
        values_2d = scaled_values.reshape(-1, 1)
    elif scaled_values.ndim == 2:
        values_2d = scaled_values
    else:
        raise ValueError("Dữ liệu chỉ được có 1 hoặc 2 chiều.")

    original_values = scaler.inverse_transform(values_2d)

    return original_values.reshape(original_shape)


def fit_scaler(
    values: np.ndarray
) -> StandardScaler:
    """
    Huấn luyện StandardScaler trên dữ liệu đầu vào.
    """

    values = np.asarray(values, dtype=np.float32)

    if values.size == 0:
        raise ValueError("Dữ liệu đầu vào không được rỗng.")

    if values.ndim == 1:
        values = values.reshape(-1, 1)
    elif values.ndim != 2:
        raise ValueError("Dữ liệu chỉ được có 1 hoặc 2 chiều.")

    scaler = StandardScaler()
    scaler.fit(values)

    return scaler

