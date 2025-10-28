import numpy as np
from scipy.signal import find_peaks as scipy_find_peaks


def find_peaks(x: np.ndarray,
               height: float = 700,
               distance: int = 10000,
               prominence: float = 150) -> np.ndarray:

    try:
        peaks, _ = scipy_find_peaks(
            x,
            # These parameters need to be tweaked to show peaks more accurately
            height=height,
            distance=distance,
            prominence=prominence
        )
        return peaks
    except Exception as e:
        print("Error finding peaks:", e)
        return np.array([])


def minmax_downsample(x: np.ndarray,
                      y: np.ndarray,
                      n_bins: int | None = None,
                      canvas_width: int | None = None) -> tuple[np.ndarray, np.ndarray]:

    N = len(y)

    if N <= 2000:
        return x, y

    if n_bins is None:
        n_bins = max(canvas_width or 0, 2000)

    bins = np.linspace(0, N, n_bins + 1, dtype=int)
    y_min = np.minimum.reduceat(y, bins[:-1])
    y_max = np.maximum.reduceat(y, bins[:-1])
    x_mid = x[(bins[:-1] + bins[1:]) // 2]

    out_len = 2 * len(x_mid)
    x_minmax = np.empty(out_len, dtype=x.dtype)
    y_minmax = np.empty(out_len, dtype=y.dtype)

    x_minmax[0::2] = x_mid
    x_minmax[1::2] = x_mid
    y_minmax[0::2] = y_min
    y_minmax[1::2] = y_max

    return x_minmax, y_minmax
