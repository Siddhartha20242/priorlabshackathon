import json
import numpy as np, pandas as pd
from sklearn.metrics import f1_score
te = pd.read_csv("data/test_with_scores.csv", parse_dates=["date"]).set_index("date")
P = json.load(open("data/threshold_params.json")); R = json.load(open("data/tabpfn_rich_results.json"))
flags = {
 "rain_3d > 77 (tuned on test)": te.rain_3d > 77,
 f"rain_3d > {P['rain3d_X']} (train-tuned)": te.rain_3d > P["rain3d_X"],
 "I-D as published": te.idscore > 1.0,
 f"I-D scale {P['id_scale']} (train-tuned)": te.idscore > P["id_scale"],
 "API k=.9 >77 (as quoted)": te["api_0.9"] > 77,
 f"API k={P['api_k']} >{P['api_thr']} (train-tuned)": te[f"api_{P['api_k']}"] > P["api_thr"],
 f"TabPFN v2 rich feats (thr {R['threshold']})": te.p_rich >= R["threshold"],
}
y = te.label.values; rng = np.random.default_rng(0); n = len(te)
idx = rng.integers(0, n, size=(2000, n))
tab = list(flags)[-1]
print(f"{'method':46s} {'F1':>5s}  95% bootstrap CI   flagged | per-year F1 (2022/23/24) | paired dF1 vs TabPFN, P(TabPFN better)")
for name, f in flags.items():
    f = f.values.astype(int); fb = flags[tab].values.astype(int)
    boots = np.array([f1_score(y[i], f[i], zero_division=0) for i in idx]); lo, hi = np.percentile(boots, [2.5, 97.5])
    d = np.array([f1_score(y[i], fb[i], zero_division=0) - f1_score(y[i], f[i], zero_division=0) for i in idx])
    py = [f1_score(y[te.index.year == yr], f[te.index.year == yr], zero_division=0) for yr in (2022, 2023, 2024)]
    print(f"{name:46s} {f1_score(y, f):5.3f}  [{lo:.2f}, {hi:.2f}]   {f.sum():4d}   | {py[0]:.2f}/{py[1]:.2f}/{py[2]:.2f} | " + ("-" if name == tab else f"{d.mean():+.3f}, {np.mean(d > 0):.0%}"))
print("positives per test year:", {yr: int(y[te.index.year == yr].sum()) for yr in (2022, 2023, 2024)}, "| days per year:", {yr: int((te.index.year == yr).sum()) for yr in (2022, 2023, 2024)})
