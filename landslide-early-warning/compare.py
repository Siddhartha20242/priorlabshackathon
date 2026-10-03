import json
import pandas as pd
from sklearn.metrics import roc_auc_score
from features import load_splits

train, test = load_splits()
b = json.load(open("data/baseline.json")); t = json.load(open("data/tabpfn_results.json")); meta = json.load(open("models/meta.json"))
from sklearn.metrics import precision_score, recall_score, f1_score
def row(name, p, auc):
    return dict(model=name, precision=precision_score(test.label, p, zero_division=0), recall=recall_score(test.label, p), f1=f1_score(test.label, p, zero_division=0), roc_auc=auc)
auc3 = roc_auc_score(test.label, test.rain_3d)
rows = [
    row(f"Baseline rain_3d > {b['best_train_X']} mm (X tuned on TRAIN)", (test.rain_3d > b["best_train_X"]).astype(int), auc3),
    row(f"Baseline rain_3d > {b['best_test_X']} mm (X tuned on TEST, optimistic)", (test.rain_3d > b["best_test_X"]).astype(int), auc3),
    row(f"TabPFN {meta['tabpfn_version']} (thr {meta['tabpfn_threshold']}, LOSO on train)", (pd.read_json("data/tabpfn_test_proba.json", typ="series") if False else __import__("numpy").load("data/tabpfn_test_proba.npy") >= meta["tabpfn_threshold"]).astype(int), t["auc"]),
]
df = pd.DataFrame(rows).set_index("model").round(3)
print(df.to_string())
print("\nTrain-season ROC-AUC of rain_3d alone:", round(roc_auc_score(train.label, train.rain_3d), 3))
for f in ["rain_today", "rain_7d", "rain_14d"]:
    print(f"test ROC-AUC of {f} alone:", round(roc_auc_score(test.label, test[f]), 3))
df.to_csv("data/comparison.csv")
