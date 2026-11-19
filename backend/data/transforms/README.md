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

    original_shape = values.shape

    values_2d = values.reshape(-1, 1)

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
        scaled_values, dtype=np.float32
    )

    original_shape = scaled_values.shape

    values_2d = scaled_values.reshape(-1, 1)

    original_values = scaler.inverse_transform(values_2d)

    return original_values.reshape(original_shape)

