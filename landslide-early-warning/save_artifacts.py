"""Consolidate everything predict.py needs into models/meta.json (model itself is models/tabpfn.joblib)."""
import json
from features import FEATURES, load_splits

train, _ = load_splits()
meta = json.load(open("models/meta.json"))
b = json.load(open("data/baseline.json"))
meta.update(
    features=FEATURES,
    baseline_threshold_train_tuned=b["best_train_X"],
    baseline_threshold_test_tuned=b["best_test_X"],
    train_medians={f: float(train[f].median()) for f in ("rain_3d", "rain_7d", "rain_14d")},
    trained_on_district="Kaski",
)
json.dump(meta, open("models/meta.json", "w"), indent=1)
print(json.dumps(meta, indent=1))
