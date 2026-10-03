"""Hourly precipitation + soil moisture (ERA5-Land via Open-Meteo archive) for the Kaski centroid, 2015-01-01 -> 2026-10-03."""
import json, time
import pandas as pd, requests
c = json.load(open("data/raw/district_centroids.json"))["Kaski"]
frames = []
for y in range(2015, 2027):
    end = f"{y}-12-31" if y < 2026 else "2026-10-03"
    for attempt in range(4):
        try:
            r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=120, params=dict(
                latitude=c["lat"], longitude=c["lon"], start_date=f"{y}-01-01", end_date=end, timezone="Asia/Kathmandu",
                hourly="precipitation,soil_moisture_0_to_7cm"))
            if r.status_code < 500: break
        except requests.RequestException: pass
        time.sleep(2 ** attempt)
    r.raise_for_status(); h = r.json()["hourly"]
    frames.append(pd.DataFrame(h)); print(y, len(h["time"]), end=" | ", flush=True)
df = pd.concat(frames); df["time"] = pd.to_datetime(df["time"]); df = df.set_index("time")
df.to_csv("data/raw/rainfall_hourly.csv")
print("\nrows", len(df), "range", df.index.min(), "->", df.index.max(), "| null precip", df.precipitation.isna().sum(), "| null soil", df.soil_moisture_0_to_7cm.isna().sum())
