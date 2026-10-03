import json, os
import numpy as np
import joblib
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from tabpfn import TabPFNClassifier
from tabpfn.constants import ModelVersion
from features import FEATURES, load_splits

train, test = load_splits()
Xtr, ytr, Xte, yte = train[FEATURES], train.label, test[FEATURES], test.label


VERSION = os.environ.get("TABPFN_VERSION", "v2")  # v2 is ungated; v2.5+ need license acceptance on ux.priorlabs.ai


def new():
    return TabPFNClassifier.create_default_for_version(ModelVersion(VERSION), random_state=0)


# threshold from leave-one-season-out on TRAIN only (no test leakage)
oof = np.zeros(len(train))
years = train.index.year.values
for y in np.unique(years):
    m = years == y
    if ytr[~m].sum() == 0 or ytr[m].sum() == 0:
        pass
    c = new().fit(Xtr[~m], ytr[~m])
    oof[m] = c.predict_proba(Xtr[m])[:, 1]
grid = np.round(np.arange(0.02, 0.9, 0.01), 2)
f1s = [f1_score(ytr, oof >= t, zero_division=0) for t in grid]
thr = float(grid[int(np.argmax(f1s))])
print(f"OOF-train ROC-AUC {roc_auc_score(ytr, oof):.3f}; chosen threshold {thr} (train OOF F1 {max(f1s):.3f})")

clf = new().fit(Xtr, ytr)
p = clf.predict_proba(Xte)[:, 1]
out = {"auc": roc_auc_score(yte, p)}
for name, t in (("thr_oof", thr), ("thr_0.5", 0.5)):
    pr = (p >= t).astype(int)
    out[name] = dict(threshold=t, precision=precision_score(yte, pr, zero_division=0), recall=recall_score(yte, pr), f1=f1_score(yte, pr, zero_division=0))
print(json.dumps(out, indent=1, default=float))
os.makedirs("models", exist_ok=True)
joblib.dump(clf, "models/tabpfn.joblib")
json.dump({"features": FEATURES, "tabpfn_threshold": thr, "tabpfn_version": VERSION}, open("models/meta.json", "w"))
json.dump(out, open("data/tabpfn_results.json", "w"), default=float)
np.save("data/tabpfn_test_proba.npy", p)
