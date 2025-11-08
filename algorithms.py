import numpy as np
from scipy.signal import find_peaks as scipy_find_peaks


def compute_baseline(signal):
    lower, upper = np.percentile(signal, [5, 95])
    trimmed = signal[(signal >= lower) & (signal <= upper)]
    return np.median(trimmed)


def find_peaks(x: np.ndarray,
               baseline: float = None,
               distance: int = 9000,
               prominence: float = 30,
               local_dist: int = 4500) -> tuple[np.ndarray, np.ndarray]:


    try:
        peaks, properties = scipy_find_peaks(
            x,
            height=baseline + 13,
            distance=distance,
            prominence=prominence
        )

        tumor_peaks = []
        water_peaks = []

        for i, peak_index in enumerate(peaks):

            start = max(0, peak_index - local_dist)
            end = min(len(x), peak_index + local_dist)
            local_area = x[start:end]

            local_min = min(local_area)

            if local_min < baseline - 15:
                water_peaks.append(peak_index)
            else:
                tumor_peaks.append(peak_index)

        return np.array(tumor_peaks), np.array(water_peaks)

    except Exception as e:
        print("Error finding peaks:", e)
        return np.array([]), np.array([])


def minmax_downsample(x: np.ndarray,
                      y: np.ndarray,
                      n_bins: int | None = None,
                      canvas_width: int | None = None) -> tuple[np.ndarray, np.ndarray]:

    n = len(y)

    if n <= 2000:
        return x, y

    if n_bins is None:
        n_bins = max(canvas_width or 0, 2000)

    bins = np.linspace(0, n, n_bins + 1, dtype=int)
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