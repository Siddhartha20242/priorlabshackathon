"""Monte Carlo risk: sample rainfall scenarios, apply the I-D rule to each, report the fraction that fire."""
import json, pathlib, time
import numpy as np, pandas as pd, requests
from thresholds import ID_DURATIONS_H, id_threshold

CENTROIDS = json.loads((pathlib.Path(__file__).parent / "data/raw/district_centroids.json").read_text())
N_SCENARIOS = 1000
ENSEMBLE_MODELS = ("ecmwf_ifs025", "gfs025", "icon_seamless")
PAST_H, FUT_H = 24 * 14, 24 * 3
RULE = json.loads((pathlib.Path(__file__).parent / "models/rule.json").read_text())
ID_SCALE = RULE["id_scale"]  # fires when mean intensity exceeds ID_SCALE x the published I-D line


def _get(url, params, tries=4):
    r = None
    for a in range(tries):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code < 500: break
        except (requests.Timeout, requests.ConnectionError):
            if a == tries - 1: raise
        time.sleep(2 ** a)
    r.raise_for_status(); return r.json()


def fetch_context(district):
    """-> dict(past (336,), central (72,), members (M,72) or None, dates, source). Hours are Nepal local time."""
    c = CENTROIDS[district]; base = dict(latitude=c["lat"], longitude=c["lon"], timezone="Asia/Kathmandu")
    d = _get("https://api.open-meteo.com/v1/forecast", {**base, "hourly": "precipitation", "past_days": 14, "forecast_days": 3})["hourly"]
    p = np.array(d["precipitation"], dtype=float)
    if len(p) != PAST_H + FUT_H or np.isnan(p).any(): raise ValueError("incomplete hourly forecast data")
    members, used = [], []
    for m in ENSEMBLE_MODELS:
        try:
            h = _get("https://ensemble-api.open-meteo.com/v1/ensemble", {**base, "hourly": "precipitation", "models": m, "forecast_days": 3})["hourly"]
            a = np.array([h[k] for k in h if k.startswith("precipitation")], dtype=float)
            if a.shape[1] == FUT_H and not np.isnan(a).any(): members.append(a); used.append(f"{m} ({len(a)})")
        except Exception:
            continue
    dates = [pd.Timestamp(t).strftime("%Y-%m-%d") for t in d["time"][PAST_H::24]]
    return dict(past=p[:PAST_H], central=p[PAST_H:], members=np.vstack(members) if members else None, dates=dates,
                source=("ensemble members pooled from " + ", ".join(used)) if members else "central forecast perturbed +/-30% (ensemble unavailable)")


def id_ratio_end_of_day(series_hourly: np.ndarray, past_h: int, n_days: int):
    """series: (S, T) hourly, first past_h columns are the past. Returns (S, n_days): max over durations of mean intensity / I-D threshold
    for the window ending at the last hour of each future day."""
    cs = np.concatenate([np.zeros((series_hourly.shape[0], 1)), np.cumsum(series_hourly, axis=1)], axis=1)
    out = np.zeros((series_hourly.shape[0], n_days))
    for j in range(n_days):
        end = past_h + 24 * (j + 1)
        out[:, j] = max_ratio(cs, end)
    return out


def max_ratio(cs, end):
    return np.max([((cs[:, end] - cs[:, end - D]) / D) / id_threshold(D) for D in ID_DURATIONS_H], axis=0)


def mc_risk(ctx, n=N_SCENARIOS, seed=None):
    rng = np.random.default_rng(seed)
    if ctx["members"] is not None:
        fut = ctx["members"][rng.integers(0, len(ctx["members"]), size=n)]
    else:
        fut = ctx["central"][None, :] * rng.uniform(0.7, 1.3, size=(n, 1))
    full = np.concatenate([np.tile(ctx["past"], (n, 1)), fut], axis=1)
    ratio = id_ratio_end_of_day(full, PAST_H, 3)
    fires = (ratio > ID_SCALE).sum(axis=0)
    central_ratio = id_ratio_end_of_day(np.concatenate([ctx["past"], ctx["central"]])[None, :], PAST_H, 3)[0]
    out = []
    for j, date in enumerate(ctx["dates"]):
        out.append(dict(date=date, n_fire=int(fires[j]), n=n, pct=round(100 * fires[j] / n),
                        central_rain_mm=round(float(ctx["central"][24 * j:24 * (j + 1)].sum()), 1),
                        central_ratio=round(float(central_ratio[j] / ID_SCALE), 2), source=ctx["source"]))
    return out
