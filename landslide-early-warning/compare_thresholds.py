import json
import numpy as np, pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from thresholds import id_score, api_series, id_threshold

hourly = pd.read_csv("data/raw/rainfall_hourly.csv", parse_dates=["time"]).set_index("time")
daily = hourly.precipitation.resample("D").sum()
df = pd.read_csv("data/processed_daily.csv", parse_dates=["date"]).set_index("date")
df["idscore"] = id_score(hourly.precipitation)[hourly.index.hour == 23].set_axis(daily.index)
for k in (0.7, 0.8, 0.85, 0.9, 0.95): df[f"api_{k}"] = api_series(daily, k)
df = df.dropna(subset=["idscore", "api_0.9"])
mon = df[df.month.between(6, 9)]
tr, te = mon[mon.index.year < 2022], mon[(mon.index.year >= 2022) & (mon.index.year <= 2024)]
print("rows train/test:", len(tr), len(te), "| positives:", tr.label.sum(), te.label.sum(), "(small drop vs before: ID needs 308h warm-up)")

def m(s, flag): return dict(precision=precision_score(s.label, flag, zero_division=0), recall=recall_score(s.label, flag), f1=f1_score(s.label, flag, zero_division=0))
def best(s, col, grid):
    sc = [(f1_score(s.label, s[col] > g, zero_division=0), g) for g in grid]; return max(sc)[1]

rows = []
# 1. cumulative rain_3d
x_pub, x_tr = 77, best(tr, "rain_3d", range(10, 201))
rows += [("rain_3d > 77 mm (picked on TEST years; optimistic)", "rain_3d", 77), ("rain_3d, threshold tuned on train", "rain_3d", x_tr)]
# 2. I-D
s_tr = best(tr, "idscore", np.round(np.arange(0.2, 3.01, 0.02), 2))
rows += [("I-D as published (19.37 D^-0.6215, D 48-308 h)", "idscore", 1.0), ("I-D, scale tuned on train", "idscore", s_tr)]
# 3. API
res = [(f1_score(tr.label, tr[f"api_{k}"] > g, zero_division=0), k, g) for k in (0.7, 0.8, 0.85, 0.9, 0.95) for g in range(20, 301)]
_, k_tr, g_tr = max(res)
rows += [("API 10-day, k=0.9, 77 mm (as quoted; k assumed)", "api_0.9", 77), (f"API 10-day, k={k_tr}, threshold tuned on train", f"api_{k_tr}", g_tr)]
out = []
for name, col, thr in rows:
    r = m(te, te[col] > thr); r["roc_auc"] = roc_auc_score(te.label, te[col]); r["param"] = thr; out.append(dict(method=name, **r))
t = pd.DataFrame(out).set_index("method").round(3)
pd.set_option("display.width", 220); print(t.to_string())
print("\nchosen on train: rain_3d X =", x_tr, "| I-D scale =", s_tr, "| API k =", k_tr, "threshold =", g_tr)
print("I-D implied thresholds (mm over D h):", {D: round(float(id_threshold(D) * D), 1) for D in (48, 72, 120, 240, 308)})
print("train-year ROC-AUC of each score:", {c: round(roc_auc_score(tr.label, tr[c]), 3) for c in ("rain_3d", "idscore", f"api_{k_tr}")})
t.to_csv("data/threshold_comparison.csv"); json.dump({"rain3d_X": int(x_tr), "id_scale": float(s_tr), "api_k": k_tr, "api_thr": int(g_tr)}, open("data/threshold_params.json", "w"))
df.to_csv("data/processed_rich.csv")
