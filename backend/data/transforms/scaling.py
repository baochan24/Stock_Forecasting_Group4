"""TV2 transforms from PR #3, commit d52946b85a390d8af8d01c5ad7a7903a16ec8485.

These functions consume a fitted scaler; they never fit or save one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from sklearn.preprocessing import StandardScaler


def _finite_values(values: np.ndarray) -> np.ndarray:
    """Validate real numeric arrays without silently coercing strings/complex values."""
    array = np.asarray(values)
    if array.ndim not in (1, 2, 3) or array.size == 0:
        raise ValueError("Expected a non-empty 1D, 2D or 3D numeric array.")
    if array.dtype.kind not in "iuf":
        raise ValueError("Values must be real numeric values.")
    array = array.astype(np.float64)
    if not np.isfinite(array).all():
        raise ValueError("Values must be finite (no NaN or Inf).")
    return array


def _transform(values, scaler, *, inverse=False):
    from sklearn.preprocessing import StandardScaler
    from sklearn.utils.validation import check_is_fitted

    array = _finite_values(values)
    if not isinstance(scaler, StandardScaler):
        raise TypeError("scaler must be a fitted StandardScaler.")
    check_is_fitted(scaler)
    if scaler.n_features_in_ != 1:
        raise ValueError("Expected a scaler fitted on exactly one price feature.")
    operation = scaler.inverse_transform if inverse else scaler.transform
    result = operation(array.reshape(-1, 1)).reshape(array.shape)
    if not np.isfinite(result).all():
        raise ValueError("Transformation produced non-finite values.")
    return result


def scale(
    values: np.ndarray,
    scaler: StandardScaler
) -> np.ndarray:
    """
    Scale a non-empty real array of rank 1–3, preserving shape as float64.

    Accepts price vectors, (B,1)/(B,5) targets or (B,30,1) inputs.
    The caller supplies a one-feature train-fitted scaler; this never fits it.
    Raises ValueError for invalid values, NotFittedError for an unfitted scaler.
    """

    return _transform(values, scaler)


def inverse_scale(
    scaled_values: np.ndarray,
    scaler: StandardScaler
) -> np.ndarray:
    """
    Restore original units, preserving shape as float64; never refit scaler.

    Negative/zero scaled values are valid. Validation follows scale().
    """

    return _transform(scaled_values, scaler, inverse=True)
