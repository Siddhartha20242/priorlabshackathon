"""Three landslide-trigger rules on rainfall: cumulative 3-day, intensity-duration (I-D), antecedent precipitation index (API)."""
import numpy as np
import pandas as pd

# I = 19.37 * D^-0.6215 (I mm/h, D hours). Published for Kanti Roadway (Bagmati Province), valid for D = 48-308 h.
ID_A, ID_B = 19.37, -0.6215
ID_DURATIONS_H = (48, 72, 96, 120, 168, 240, 308)


def id_threshold(duration_h, scale=1.0):
    """Intensity (mm/h) above which a rainfall of the given duration is flagged."""
    return scale * ID_A * np.asarray(duration_h, dtype=float) ** ID_B


def id_flag(intensity_mm_h, duration_h, scale=1.0):
    """True when mean intensity over the duration exceeds the I-D threshold."""
    return np.asarray(intensity_mm_h) > id_threshold(duration_h, scale)


def id_score(hourly: pd.Series, durations=ID_DURATIONS_H) -> pd.Series:
    """Hourly series -> for each hour, max over durations of (trailing mean intensity / threshold). >1 means the I-D line is crossed."""
    ratios = [(hourly.rolling(D).sum() / D) / id_threshold(D) for D in durations]
    return pd.concat(ratios, axis=1).max(axis=1)


def api_series(daily: pd.Series, k: float = 0.9, days: int = 10) -> pd.Series:
    """API_t = sum_{i=0}^{days-1} k^i * P_{t-i}, today included. Decay k is not given in the sources I could read, so it is tuned."""
    w = k ** np.arange(days)
    return daily.rolling(days).apply(lambda x: float(np.dot(x[::-1], w)), raw=True)
