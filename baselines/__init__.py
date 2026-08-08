"""Baseline model registry (B01 families) — implementations live in framework.ecn.models."""
from ecn.models import fit_binary, predict_scores

BASELINE_NAMES = [
    "majority",
    "threshold",
    "ewma",
    "isolation_forest",
    "logistic",
    "random_forest",
    "gradient_boosting",
    "balanced_rf",
    "lightgbm",
    "xgboost",
    "catboost",
    "mlp_sequence",
]

__all__ = ["BASELINE_NAMES", "fit_binary", "predict_scores"]
