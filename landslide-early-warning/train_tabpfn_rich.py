"""TabPFN v2 (Apache-2.0 + attribution weights, ungated) on richer features. Same split and threshold method as before."""
import json
import numpy as np, pandas as pd, joblib
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from tabpfn import TabPFNClassifier
from tabpfn.constants import ModelVersion

hourly = pd.read_csv("data/raw/rainfall_hourly.csv", parse_dates=["time"]).set_index("time")
rain = hourly.precipitation.resample("D").sum()
df = pd.read_csv("data/processed_rich.csv", parse_dates=["date"]).set_index("date")
df["soil_0_7cm"] = hourly.soil_moisture_0_to_7cm.resample("D").mean().reindex(df.index)
for L in (1, 3, 5, 7, 10, 14): df[f"lag{L}"] = rain.shift(L).reindex(df.index)
FEATS = ["rain_today", "lag1", "lag3", "lag5", "lag7", "lag10", "lag14", "rain_3d", "api_0.9", "api_0.7", "soil_0_7cm", "month"]
mon = df[df.month.between(6, 9)].dropna(subset=FEATS)
tr, te = mon[mon.index.year < 2022], mon[(mon.index.year >= 2022) & (mon.index.year <= 2024)]
print("train/test rows:", len(tr), len(te), "| positives:", tr.label.sum(), te.label.sum(), "| season is constant (monsoon only) -> not used")
new = lambda: TabPFNClassifier.create_default_for_version(ModelVersion.V2, random_state=0)

oof = np.zeros(len(tr)); yrs = tr.index.year.values
for y in np.unique(yrs):
    mk = yrs == y
    oof[mk] = new().fit(tr.loc[~mk, FEATS], tr.label[~mk]).predict_proba(tr.loc[mk, FEATS])[:, 1]
grid = np.round(np.arange(0.02, 0.9, 0.01), 2)
thr = float(grid[int(np.argmax([f1_score(tr.label, oof >= t, zero_division=0) for t in grid]))])
print(f"leave-one-season-out on train: ROC-AUC {roc_auc_score(tr.label, oof):.3f}, chosen threshold {thr}")
clf = new().fit(tr[FEATS], tr.label); p = clf.predict_proba(te[FEATS])[:, 1]
pr = (p >= thr).astype(int)
res = dict(precision=precision_score(te.label, pr, zero_division=0), recall=recall_score(te.label, pr), f1=f1_score(te.label, pr, zero_division=0),
           roc_auc=roc_auc_score(te.label, p), threshold=thr, flagged=int(pr.sum()), oof_train_auc=roc_auc_score(tr.label, oof))
print(json.dumps(res, indent=1, default=float))
joblib.dump(clf, "models/tabpfn_rich.joblib"); np.save("data/tabpfn_rich_test_proba.npy", p); json.dump({**res, "features": FEATS}, open("data/tabpfn_rich_results.json", "w"), default=float)
te.assign(p_rich=p).to_csv("data/test_with_scores.csv")
