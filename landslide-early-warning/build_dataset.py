import sys
import pandas as pd
from features import rain_features

DISTRICT = sys.argv[1] if len(sys.argv) > 1 else "Kaski"

rain = pd.read_csv("data/raw/rainfall.csv", parse_dates=["date"]).set_index("date")["precipitation_sum"]
rain = rain.asfreq("D")
missing = int(rain.isna().sum())
rain = rain.ffill()
print(f"missing rainfall days forward-filled: {missing} of {len(rain)}")

inc = pd.read_csv("data/raw/incidents_with_district.csv")
days = pd.to_datetime(inc.loc[inc.district == DISTRICT, "date"]).unique()

df = rain_features(rain)
n0 = len(df)
df = df.dropna()
print(f"dropped {n0 - len(df)} leading days with incomplete 14-day window")
df["label"] = df.index.isin(days).astype(int)
df.index.name = "date"
df.to_csv("data/processed_daily.csv")

print(f"\nall days: {len(df)}  positives: {df.label.sum()}  rate: {df.label.mean():.3%}")
off = df[(df.label == 1) & ~df.month.between(6, 9)]
print(f"landslide days outside Jun-Sep: {len(off)} of {df.label.sum()}")
mon = df[df.month.between(6, 9)]
print(f"monsoon (Jun-Sep) days: {len(mon)}  positives: {mon.label.sum()}  rate: {mon.label.mean():.3%}")
