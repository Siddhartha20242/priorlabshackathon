"""Shared feature code, so training and the app compute features identically."""
import pandas as pd

FEATURES = ["rain_today", "rain_3d", "rain_7d", "rain_14d", "month"]


def rain_features(daily: pd.Series) -> pd.DataFrame:
    """daily: rainfall in mm indexed by a daily DatetimeIndex. Windows are trailing and include today."""
    out = pd.DataFrame({"rain_today": daily})
    for n in (3, 7, 14):
        out[f"rain_{n}d"] = daily.rolling(n, min_periods=n).sum()
    out["month"] = daily.index.month
    return out


def load_splits(path="data/processed_daily.csv"):
    """Monsoon (Jun-Sep) days only. Train: before 2022. Test: 2022-2024. No shuffling."""
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    mon = df[df.month.between(6, 9)]
    return mon[mon.index.year < 2022], mon[(mon.index.year >= 2022) & (mon.index.year <= 2024)]
