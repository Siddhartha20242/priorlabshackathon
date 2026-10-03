import json
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from features import load_splits

train, test = load_splits()
for name, s in (("train (monsoon <2022)", train), ("test (monsoon 2022-2024)", test)):
    print(f"{name}: rows={len(s)} positives={s.label.sum()} positive_rate={s.label.mean():.3%}")


def score(s, x):
    p = (s.rain_3d > x).astype(int)
    return (precision_score(s.label, p, zero_division=0), recall_score(s.label, p), f1_score(s.label, p))


xs = list(range(10, 201))
res = pd.DataFrame([(x, *score(test, x)) for x in xs], columns=["X_mm", "precision", "recall", "f1"]).set_index("X_mm")
tr = pd.DataFrame([(x, *score(train, x)) for x in xs], columns=["X_mm", "precision", "recall", "f1"]).set_index("X_mm")
print("\nTest-set sweep (every 10 mm):\n", res.loc[list(range(10, 201, 10))].round(3).to_string())
best_test = res.f1.idxmax()
best_train = tr.f1.idxmax()
print(f"\nBest X on TEST (as requested; optimistic, tuned on test): X={best_test} ->", res.loc[best_test].round(3).to_dict())
print(f"X chosen on TRAIN (honest):                              X={best_train} -> test", res.loc[best_train].round(3).to_dict())
json.dump({"best_test_X": int(best_test), "best_train_X": int(best_train)}, open("data/baseline.json", "w"))
