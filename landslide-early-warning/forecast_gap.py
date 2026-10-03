"""Archive (ERA5-based reanalysis, what the model trained on) vs archived Open-Meteo forecasts, Kaski centroid."""
import json, datetime as dt
import numpy as np, pandas as pd, requests

c = json.load(open("data/raw/district_centroids.json"))["Kaski"]
BASE = dict(latitude=c["lat"], longitude=c["lon"], timezone="Asia/Kathmandu")


def get(url, start, end, **kw):
    r = requests.get(url, params={**BASE, "start_date": str(start), "end_date": str(end), **kw}, timeout=90); r.raise_for_status()
    return r.json()


def window(start, end):
    a = get("https://archive-api.open-meteo.com/v1/archive", start, end, daily="precipitation_sum")["daily"]
    arch = pd.Series(a["precipitation_sum"], index=pd.to_datetime(a["time"]), dtype=float)
    h = get("https://previous-runs-api.open-meteo.com/v1/forecast", start, end,
            hourly="precipitation,precipitation_previous_day1,precipitation_previous_day2")["hourly"]
    hh = pd.DataFrame(h); hh["d"] = pd.to_datetime(hh.pop("time")).dt.normalize()
    daily = hh.groupby("d").sum(min_count=1)
    return arch, daily


def report(label, start, end):
    arch, f = window(start, end)
    print(f"\n### {label}: {start} -> {end} ({len(arch)} days; mean daily archive rain {arch.mean():.1f} mm, max {arch.max():.1f})")
    for col, name in (("precipitation", "day-0 (latest run)"), ("precipitation_previous_day1", "1 day ahead"), ("precipitation_previous_day2", "2 days ahead")):
        x = pd.concat([arch.rename("a"), f[col].rename("f")], axis=1).dropna()
        if len(x) < 5: print(f"  {name}: not enough data ({len(x)} days)"); continue
        e = x.f - x.a
        a3, f3 = x.a.rolling(3).sum().dropna(), x.f.rolling(3).sum().dropna()
        e3 = f3 - a3
        flag = ((a3 > 77) == (f3 > 77))
        print(f"  {name:20s} n={len(x):3d} | daily MAE {e.abs().mean():5.1f} mm, bias {e.mean():+5.1f} mm | 3-day-total MAE {e3.abs().mean():5.1f} mm, bias {e3.mean():+6.1f} mm | rain_3d>77 rule agrees on {flag.mean():.0%} of days; archive>77 on {(a3>77).sum()} days, forecast>77 on {(f3>77).sum()}")
    return arch, f


end = dt.date.today() - dt.timedelta(days=2)
report("LAST 30 DAYS (as requested)", end - dt.timedelta(days=29), end)
report("2025 MONSOON (Jun-Sep)", dt.date(2025, 6, 1), dt.date(2025, 9, 30))
