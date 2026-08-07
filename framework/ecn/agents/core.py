"""Multi-agent components of the Enterprise Cognitive Network."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from ..models import (
    FitResult,
    eval_binary,
    eval_multiclass,
    fit_binary,
    fit_multiclass,
    predict_scores,
    tune_threshold,
)


@dataclass
class AgentReport:
    agent: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    train_time_s: float = 0.0
    infer_time_s: float = 0.0
    explanations: Optional[List[Dict[str, Any]]] = None


class PerceptionAgent:
    """Builds twin-aware feature views (constructed upstream via DigitalTwin)."""

    name = "PerceptionAgent"

    def describe(self, feature_cols: List[str]) -> Dict[str, Any]:
        twin_cols = [c for c in feature_cols if c.startswith("twin_")]
        telem = [
            c
            for c in feature_cols
            if c
            in (
                "cpu_mean",
                "cpu_max",
                "mem_mean",
                "err_sum",
                "disc_sum",
                "car_sum",
                "n_polls",
            )
        ]
        return {
            "n_features": len(feature_cols),
            "n_twin_features": len(twin_cols),
            "n_telemetry_features": len(telem),
            "twin_features": twin_cols,
        }


class AnomalyAgent:
    name = "AnomalyAgent"

    def __init__(self, backend: str = "ecn_stack", seed: int = 0):
        self.backend = backend
        self.seed = seed
        self.fit: Optional[FitResult] = None
        self.threshold = 0.5

    def train(self, X_tr, y_tr, X_va, y_va) -> AgentReport:
        self.fit = fit_binary(self.backend, X_tr, y_tr, seed=self.seed)
        scores = predict_scores(self.fit, X_va)
        self.threshold = tune_threshold(y_va, scores)
        return AgentReport(
            agent=self.name,
            train_time_s=self.fit.train_time_s,
            metrics={"val_threshold": self.threshold},
        )

    def evaluate(self, X_te, y_te) -> AgentReport:
        import time

        t0 = time.perf_counter()
        scores = predict_scores(self.fit, X_te)
        dt = time.perf_counter() - t0
        metrics = eval_binary(y_te, scores, self.threshold)
        metrics["backend"] = self.backend
        return AgentReport(
            agent=self.name,
            metrics=metrics,
            infer_time_s=dt,
            train_time_s=self.fit.train_time_s,
        )


class PredictionAgent:
    name = "PredictionAgent"

    def __init__(self, backend: str = "ecn_stack", seed: int = 0):
        self.backend = backend
        self.seed = seed
        self.fit: Optional[FitResult] = None
        self.threshold = 0.5

    def train(self, X_tr, y_tr, X_va, y_va) -> AgentReport:
        self.fit = fit_binary(self.backend, X_tr, y_tr, seed=self.seed)
        self.threshold = tune_threshold(y_va, predict_scores(self.fit, X_va))
        return AgentReport(agent=self.name, train_time_s=self.fit.train_time_s)

    def evaluate(self, X_te, y_te) -> AgentReport:
        import time

        t0 = time.perf_counter()
        scores = predict_scores(self.fit, X_te)
        dt = time.perf_counter() - t0
        metrics = eval_binary(y_te, scores, self.threshold)
        metrics["backend"] = self.backend
        return AgentReport(
            agent=self.name,
            metrics=metrics,
            infer_time_s=dt,
            train_time_s=self.fit.train_time_s,
        )


class RCAAgent:
    """Explainable RCA: category classification + feature importances."""

    name = "RCAAgent"

    def __init__(self, seed: int = 0):
        self.seed = seed
        self.model = None
        self.le = None
        self.feature_cols: List[str] = []
        self.train_time_s = 0.0

    def train(self, X_tr, y_tr, feature_cols: List[str]) -> AgentReport:
        self.feature_cols = feature_cols
        self.model, self.le, self.train_time_s = fit_multiclass(X_tr, y_tr, seed=self.seed)
        return AgentReport(agent=self.name, train_time_s=self.train_time_s)

    def evaluate(self, X_te, y_te) -> AgentReport:
        import time

        t0 = time.perf_counter()
        metrics = eval_multiclass(self.model, self.le, X_te, y_te)
        dt = time.perf_counter() - t0
        imp = getattr(self.model, "feature_importances_", None)
        explanations: List[Dict[str, Any]] = []
        if imp is not None:
            order = np.argsort(-imp)[:10]
            explanations = [
                {"feature": self.feature_cols[i], "importance": float(imp[i])}
                for i in order
                if i < len(self.feature_cols)
            ]
        metrics["top_explanatory_features"] = explanations
        # TreeSHAP (fallback: already have impurity importances)
        shap_top: List[Dict[str, Any]] = []
        try:
            import shap  # type: ignore

            explainer = shap.TreeExplainer(self.model)
            # sample for speed
            Xs = X_te if len(X_te) <= 64 else X_te[:64]
            sv = explainer.shap_values(Xs)
            if isinstance(sv, list):
                # multiclass: average abs across classes
                arr = np.mean([np.abs(s) for s in sv], axis=0)
            else:
                arr = np.abs(sv)
            mean_abs = arr.mean(axis=0)
            order = np.argsort(-mean_abs)[:10]
            shap_top = [
                {"feature": self.feature_cols[i], "mean_abs_shap": float(mean_abs[i])}
                for i in order
                if i < len(self.feature_cols)
            ]
            metrics["shap_top_features"] = shap_top
            if shap_top:
                explanations = shap_top
        except Exception as e:
            metrics["shap_error"] = str(e)[:200]
        return AgentReport(
            agent=self.name,
            metrics=metrics,
            infer_time_s=dt,
            train_time_s=self.train_time_s,
            explanations=explanations,
        )


class ImpactAgent:
    """Service impact prediction (T4) from twin + early telemetry."""

    name = "ImpactAgent"

    def __init__(self, seed: int = 0):
        self.seed = seed
        self.fit: Optional[FitResult] = None
        self.threshold = 0.5

    def train(self, X_tr, y_tr, X_va, y_va) -> AgentReport:
        self.fit = fit_binary("ecn_stack", X_tr, y_tr, seed=self.seed)
        self.threshold = tune_threshold(y_va, predict_scores(self.fit, X_va))
        return AgentReport(agent=self.name, train_time_s=self.fit.train_time_s)

    def evaluate(self, X_te, y_te) -> AgentReport:
        import time

        t0 = time.perf_counter()
        scores = predict_scores(self.fit, X_te)
        dt = time.perf_counter() - t0
        metrics = eval_binary(y_te, scores, self.threshold)
        return AgentReport(
            agent=self.name,
            metrics=metrics,
            infer_time_s=dt,
            train_time_s=self.fit.train_time_s,
        )


class HealingAgent:
    """Self-healing decision support: recommend recovery action type."""

    name = "HealingAgent"

    def __init__(self, seed: int = 0):
        self.seed = seed
        self.model = None
        self.le = None
        self.feature_cols: List[str] = []
        self.train_time_s = 0.0

    def train(self, X_tr, y_tr, feature_cols: List[str]) -> AgentReport:
        self.feature_cols = feature_cols
        self.model, self.le, self.train_time_s = fit_multiclass(X_tr, y_tr, seed=self.seed)
        return AgentReport(agent=self.name, train_time_s=self.train_time_s)

    def evaluate(self, X_te, y_te) -> AgentReport:
        import time

        t0 = time.perf_counter()
        metrics = eval_multiclass(self.model, self.le, X_te, y_te)
        dt = time.perf_counter() - t0
        return AgentReport(
            agent=self.name,
            metrics=metrics,
            infer_time_s=dt,
            train_time_s=self.train_time_s,
        )


class Orchestrator:
    """Coordinates digital-twin perception and specialist agents (proposed ECN)."""

    name = "ECN-Orchestrator"

    def __init__(self, seed: int = 0):
        self.seed = seed
        self.perception = PerceptionAgent()
        self.anomaly = AnomalyAgent(backend="ecn_stack", seed=seed)
        self.prediction = PredictionAgent(backend="ecn_stack", seed=seed)
        self.rca = RCAAgent(seed=seed)
        self.impact = ImpactAgent(seed=seed)
        self.healing = HealingAgent(seed=seed)
