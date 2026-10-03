import json
import time
import pathlib
import datetime as dt
import pandas as pd
import requests

CENTROIDS = json.loads((pathlib.Path(__file__).parent / "data/raw/district_centroids.json").read_text())
DISTRICTS = ["Gorkha", "Kaski", "Lamjung", "Tanahun", "Syangja", "Parbat", "Myagdi", "Baglung", "Manang", "Mustang"]
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
def _fetch(district: str, past_days: int, forecast_days: int) -> pd.Series:
    c = CENTROIDS[district]
    params = dict(latitude=c["lat"], longitude=c["lon"], daily="precipitation_sum", timezone="Asia/Kathmandu",
                  past_days=past_days, forecast_days=forecast_days)
    r = None
    for attempt in range(4):  # Open-Meteo occasionally returns 5xx or times out; back off and retry
        try:
            r = requests.get(FORECAST_URL, params=params, timeout=20)
            if r.status_code < 500:
                break
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)
    r.raise_for_status()
    d = r.json()["daily"]
    return pd.Series(d["precipitation_sum"], index=pd.to_datetime(d["time"]), dtype="float64")


def get_forecast(district: str, days: int = 3) -> list[dict]:
    """Next `days` days of forecast rainfall, starting today (Nepal time): [{date, rain_mm}]."""
    s = _fetch(district, past_days=0, forecast_days=days)
    return [{"date": d.strftime("%Y-%m-%d"), "rain_mm": None if pd.isna(v) else float(v)} for d, v in s.items()]


def get_last_14_days(district: str) -> list[dict]:
    """The 14 complete days before today, from the same API's past_days analysis data."""
    s = _fetch(district, past_days=14, forecast_days=1).iloc[:14]
    return [{"date": d.strftime("%Y-%m-%d"), "rain_mm": float(v)} for d, v in s.items()]


def check_district(district: str) -> list[dict]:
    """Monte Carlo risk for today and the next 2 days: fraction of 1,000 rainfall scenarios that cross the I-D rule."""
    from mc import fetch_context, mc_risk
    return mc_risk(fetch_context(district))
