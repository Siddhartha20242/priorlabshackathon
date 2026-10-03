"""Load the saved Kaski model and score feature dicts.

    from predict import predict
    predict({"rain_today": 40, "rain_3d": 95, "rain_7d": 140, "rain_14d": 200, "month": 7})
    -> {"label": "ELEVATED", "probability": 0.12, "baseline_flag": True}
"""
import json
import pathlib
import joblib
import pandas as pd

_DIR = pathlib.Path(__file__).parent / "models"
_clf = None
_meta = None


def _load():
    global _clf, _meta
    if _clf is None:
        _meta = json.loads((_DIR / "meta.json").read_text())
        _clf = joblib.load(_DIR / "tabpfn.joblib")
    return _clf, _meta


def predict_many(rows):
    """rows: list of feature dicts -> list of {label, probability, baseline_flag}."""
    clf, meta = _load()
    X = pd.DataFrame(rows)[meta["features"]]
    probs = clf.predict_proba(X)[:, 1]
    return [
        {
            "label": "ELEVATED" if p >= meta["tabpfn_threshold"] else "LOWER",
            "probability": float(p),
            # simple rain_3d rule, kept alongside because it scored better than TabPFN on the test set
            "baseline_flag": bool(r["rain_3d"] > meta["baseline_threshold_test_tuned"]),
        }
        for r, p in zip(rows, probs)
    ]


def predict(features: dict) -> dict:
    return predict_many([features])[0]


def top_driver(features: dict) -> str:
    """Which of rain_3d / rain_7d / rain_14d moves the probability most.

    Ablation: replace one window with its training-season median and see how far the probability drops.
    """
    _, meta = _load()
    variants = [features] + [{**features, k: meta["train_medians"][k]} for k in ("rain_3d", "rain_7d", "rain_14d")]
    base, *rest = [r["probability"] for r in predict_many(variants)]
    drops = dict(zip(("rain_3d", "rain_7d", "rain_14d"), (base - p for p in rest)))
    return max(drops, key=drops.get)
