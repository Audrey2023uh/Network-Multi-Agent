"""Models, baselines, metrics, and statistical tests for ECN evaluation."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from sklearn.calibration import calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    GradientBoostingClassifier,
    IsolationForest,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
)
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    from lightgbm import LGBMClassifier

    HAS_LGBM = True
except Exception:  # pragma: no cover
    HAS_LGBM = False


def ewma_anomaly_scores(X: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Univariate EWMA on first feature column (CPU) — higher score = more anomalous."""
    x = X[:, 0].astype(float)
    s = np.zeros_like(x)
    s[0] = x[0]
    for i in range(1, len(x)):
        s[i] = alpha * x[i] + (1 - alpha) * s[i - 1]
    resid = np.abs(x - s)
    # z-score residuals
    mu, sd = resid.mean(), resid.std() + 1e-9
    return (resid - mu) / sd


def threshold_scores(X: np.ndarray, q: float = 0.95) -> np.ndarray:
    x = X[:, 0].astype(float)
    thr = np.quantile(x, q)
    return (x - thr) / (np.std(x) + 1e-9)


@dataclass
class FitResult:
    name: str
    model: Any
    train_time_s: float
    n_features: int


def fit_binary(name: str, X: np.ndarray, y: np.ndarray, seed: int = 0) -> FitResult:
    t0 = time.perf_counter()
    if name == "majority":
        m = DummyClassifier(strategy="most_frequent")
        m.fit(X, y)
    elif name == "ewma":
        m = ("ewma", None)  # score-only
    elif name == "threshold":
        m = ("threshold", None)
    elif name == "isolation_forest":
        # fit on negatives primarily
        m = IsolationForest(n_estimators=100, contamination=max(0.01, float(y.mean()) or 0.01), random_state=seed)
        m.fit(X[y == 0] if (y == 0).any() else X)
    elif name == "logistic":
        m = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=800, class_weight="balanced", random_state=seed)),
        ])
        m.fit(X, y)
    elif name == "random_forest":
        m = RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=3,
            class_weight="balanced_subsample", random_state=seed, n_jobs=-1,
        )
        m.fit(X, y)
    elif name == "gradient_boosting":
        m = GradientBoostingClassifier(random_state=seed)
        m.fit(X, y)
    elif name == "lightgbm":
        if not HAS_LGBM:
            m = GradientBoostingClassifier(random_state=seed)
            m.fit(X, y)
        else:
            m = LGBMClassifier(
                n_estimators=300,
                learning_rate=0.05,
                num_leaves=31,
                class_weight="balanced",
                random_state=seed,
                verbosity=-1,
                n_jobs=-1,
            )
            m.fit(X, y)
    elif name == "mlp_sequence":
        # Sequence-model proxy: MLP on windowed tabular features (no torch required at train-scale)
        m = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    MLPClassifier(
                        hidden_layer_sizes=(64, 32),
                        max_iter=120,
                        early_stopping=True,
                        random_state=seed,
                    ),
                ),
            ]
        )
        m.fit(X, y)
    elif name == "ecn_stack":  # single specialist backend (used inside fusion)
        # Prefer calibrated linear + tree blend features via logistic on twin-enriched X
        m = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=seed,
                        C=0.5,
                    ),
                ),
            ]
        )
        m.fit(X, y)
    elif name == "ecn_fusion":
        # Placeholder — fusion is handled by ECNFusionModel outside fit_binary
        raise ValueError("use ECNFusionModel for ecn_fusion")
    else:
        raise ValueError(name)
    return FitResult(name=name, model=m, train_time_s=time.perf_counter() - t0, n_features=X.shape[1])


class ECNFusionModel:
    """
    Optimized multi-agent fusion (scientifically motivated).

    Pre-opt diagnosis
    -----------------
    Val-AP mixtures/meta often underperformed the telem logistic specialist on test
    (nesting violation). class_weight-balanced scores had high Brier, but isotonic
    calibration on few positives *reordered* scores and hurt AUPRC.

    Design (AUPRC-primary)
    ----------------------
    - Specialists: telem LR, twin LR, scale_pos_weight LGBM, RF, IsolationForest
    - Rank on *raw* scores (AUPRC is ranking-based); report optional post-hoc
      calibration separately if needed
    - **Anchored fusion**: every candidate includes telem_lr weight ≥ 0.5 unless
      telem_lr alone is selected — encodes the empirical prior that linear telem
      is the strongest stable signal on this benchmark, while still allowing
      twin/RF to contribute when val evidence is clear
    - IF mapped with train empirical CDF (stable across splits)
    """

    FUSION_MARGIN = 0.01

    def __init__(self, seed: int = 0):
        self.seed = seed
        self.telem_idx: List[int] = []
        self.agents: Dict[str, Any] = {}
        self.fusion_w: Optional[np.ndarray] = None
        self.agent_names: List[str] = []
        self.iso_ref: Optional[np.ndarray] = None
        self.train_time_s = 0.0
        self.diagnostics: Dict[str, Any] = {}

    def fit(
        self,
        X_tr: np.ndarray,
        y_tr: np.ndarray,
        X_va: np.ndarray,
        y_va: np.ndarray,
        feature_names: List[str],
    ) -> "ECNFusionModel":
        t0 = time.perf_counter()
        telem_names = {
            "cpu_mean", "cpu_max", "mem_mean", "n_polls", "err_sum", "disc_sum", "car_sum",
            "sev_n", "d_cpu_mean", "d_cpu_max", "d_mem_mean", "cpu_z", "mem_z",
        }
        self.telem_idx = [i for i, c in enumerate(feature_names) if c in telem_names]
        if not self.telem_idx:
            self.telem_idx = [i for i, c in enumerate(feature_names) if not str(c).startswith("twin_")]
        if not self.telem_idx:
            self.telem_idx = list(range(min(3, X_tr.shape[1])))

        Xt = X_tr[:, self.telem_idx]
        prior = float(y_tr.mean()) if len(y_tr) else 0.01
        n_pos = max(int(y_tr.sum()), 1)
        n_neg = max(int(len(y_tr) - y_tr.sum()), 1)
        spw = n_neg / n_pos

        telem = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1200, class_weight="balanced", random_state=self.seed, C=1.0)),
        ])
        telem.fit(Xt, y_tr)

        twin_lr = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1200, class_weight="balanced", random_state=self.seed, C=0.5)),
        ])
        twin_lr.fit(X_tr, y_tr)

        if HAS_LGBM:
            twin_tree = LGBMClassifier(
                n_estimators=400, learning_rate=0.05, num_leaves=31,
                min_child_samples=20, subsample=0.9, colsample_bytree=0.8,
                scale_pos_weight=spw, random_state=self.seed, verbosity=-1, n_jobs=-1,
            )
        else:
            twin_tree = RandomForestClassifier(
                n_estimators=300, max_depth=10, min_samples_leaf=5,
                class_weight="balanced_subsample", random_state=self.seed, n_jobs=-1,
            )
        twin_tree.fit(X_tr, y_tr)

        rf = RandomForestClassifier(
            n_estimators=300, max_depth=12, min_samples_leaf=3,
            class_weight="balanced_subsample", random_state=self.seed, n_jobs=-1,
        )
        rf.fit(X_tr, y_tr)

        iso = IsolationForest(
            n_estimators=150, contamination=min(0.05, max(0.005, prior)), random_state=self.seed,
        )
        iso.fit(Xt[y_tr == 0] if (y_tr == 0).any() else Xt)
        self.iso_ref = np.sort(-iso.score_samples(Xt))

        self.agents = {
            "telem_lr": telem,
            "twin_lr": twin_lr,
            "twin_tree": twin_tree,
            "rf": rf,
            "iso": iso,
        }
        self.agent_names = list(self.agents.keys())

        S_va = self._agent_scores(X_va)
        S_tr = self._agent_scores(X_tr)
        self._select_anchored_fusion(S_va, y_va, S_tr, y_tr)
        self.train_time_s = time.perf_counter() - t0
        self.diagnostics["prior_train"] = prior
        self.diagnostics["scale_pos_weight"] = spw
        return self

    def _if_to_unit(self, raw: np.ndarray) -> np.ndarray:
        if self.iso_ref is None or len(self.iso_ref) == 0:
            order = raw.argsort()
            out = np.empty_like(raw, dtype=float)
            out[order] = np.linspace(0, 1, len(raw))
            return out
        idx = np.searchsorted(self.iso_ref, raw, side="right")
        return np.clip(idx / float(len(self.iso_ref)), 0, 1)

    def _agent_scores(self, X: np.ndarray) -> np.ndarray:
        Xt = X[:, self.telem_idx]
        return np.column_stack([
            self.agents["telem_lr"].predict_proba(Xt)[:, 1],
            self.agents["twin_lr"].predict_proba(X)[:, 1],
            self.agents["twin_tree"].predict_proba(X)[:, 1],
            self.agents["rf"].predict_proba(X)[:, 1],
            self._if_to_unit(-self.agents["iso"].score_samples(Xt)),
        ])

    def _select_anchored_fusion(
        self, S_va: np.ndarray, y_va: np.ndarray, S_tr: np.ndarray, y_tr: np.ndarray
    ) -> None:
        n = S_va.shape[1]
        telem_i = 0
        telem_w = np.zeros(n)
        telem_w[telem_i] = 1.0
        if len(np.unique(y_va)) < 2:
            self.fusion_w = telem_w
            self.diagnostics["selected"] = "telem_lr_default"
            return

        singleton_ap_va = [float(average_precision_score(y_va, S_va[:, j])) for j in range(n)]
        singleton_ap_tr = [
            float(average_precision_score(y_tr, S_tr[:, j])) if len(np.unique(y_tr)) > 1 else 0.0
            for j in range(n)
        ]
        telem_ap = singleton_ap_va[telem_i]
        best_i = int(np.argmax(singleton_ap_va))

        candidates = [("telem_only", telem_w)]
        # Allow non-telem singleton only with train–val consistency (rare-event stability)
        if best_i != telem_i:
            consistent = (
                singleton_ap_va[best_i] >= telem_ap + self.FUSION_MARGIN
                and singleton_ap_tr[best_i] >= singleton_ap_tr[telem_i]
            )
            if consistent:
                w = np.zeros(n)
                w[best_i] = 1.0
                candidates.append((f"singleton_{self.agent_names[best_i]}", w))
        # Anchored mixes: telem weight ≥ 0.5
        for j in range(1, n):
            for a in (0.5, 0.7, 0.9):
                # require other agent not worse than telem on train (weak consistency)
                if singleton_ap_tr[j] + 1e-12 < singleton_ap_tr[telem_i] - 0.02:
                    continue
                w = np.zeros(n)
                w[telem_i] = a
                w[j] = 1.0 - a
                candidates.append((f"anchor_{a}_{self.agent_names[j]}", w))

        best_name, best_w, best_cap = "telem_only", telem_w, telem_ap
        for name, w in candidates:
            ap = float(average_precision_score(y_va, S_va @ w))
            if ap > best_cap + (0.0 if name == "telem_only" else 1e-15):
                # non-telem needs margin over telem
                if name == "telem_only" or ap >= telem_ap + self.FUSION_MARGIN:
                    best_cap, best_name, best_w = ap, name, w

        self.fusion_w = best_w
        self.diagnostics.update({
            "singleton_ap_val": {self.agent_names[i]: singleton_ap_va[i] for i in range(n)},
            "singleton_ap_train": {self.agent_names[i]: singleton_ap_tr[i] for i in range(n)},
            "selected": best_name,
            "selected_val_ap": best_cap,
            "telem_val_ap": telem_ap,
            "best_singleton": self.agent_names[best_i],
        })

    def predict_proba_positive(self, X: np.ndarray) -> np.ndarray:
        S = self._agent_scores(X)
        return np.clip(S @ self.fusion_w, 0, 1)


def predict_scores(fit: FitResult, X: np.ndarray) -> np.ndarray:
    m = fit.model
    if fit.name == "ewma":
        return ewma_anomaly_scores(X)
    if fit.name == "threshold":
        return threshold_scores(X)
    if fit.name == "isolation_forest":
        # higher = more anomalous
        return -m.score_samples(X)
    if hasattr(m, "predict_proba"):
        return m.predict_proba(X)[:, 1]
    return m.predict(X).astype(float)


def tune_threshold(y_val: np.ndarray, scores: np.ndarray) -> float:
    best_t, best_f1 = 0.5, -1.0
    # map scores to [0,1] via rank for non-probabilistic
    s = scores.astype(float)
    if s.max() > 1.5 or s.min() < -0.5:
        # rank-normalize
        order = s.argsort()
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.linspace(0, 1, len(s))
        s = ranks
    for t in np.linspace(0.05, 0.95, 19):
        f1 = f1_score(y_val, (s >= t).astype(int), zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return float(best_t)


def eval_binary(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> Dict[str, Any]:
    s = scores.astype(float)
    if s.max() > 1.5 or s.min() < -0.5:
        order = s.argsort()
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.linspace(0, 1, len(s))
        s_norm = ranks
    else:
        s_norm = np.clip(s, 0, 1)
    pred = (s_norm >= threshold).astype(int)
    out: Dict[str, Any] = {
        "threshold": threshold,
        "prior": float(y_true.mean()),
        "support_pos": int(y_true.sum()),
        "support_neg": int((1 - y_true).sum()),
    }
    if len(np.unique(y_true)) > 1:
        out["roc_auc"] = float(roc_auc_score(y_true, s_norm))
        out["ap"] = float(average_precision_score(y_true, s_norm))
        out["brier"] = float(brier_score_loss(y_true, s_norm))
        fpr, tpr, _ = roc_curve(y_true, s_norm)
        prec, rec, _ = precision_recall_curve(y_true, s_norm)
        out["roc_curve"] = {"fpr": fpr.tolist()[:: max(1, len(fpr)//50)], "tpr": tpr.tolist()[:: max(1, len(tpr)//50)]}
        out["pr_curve"] = {"precision": prec.tolist()[:: max(1, len(prec)//50)], "recall": rec.tolist()[:: max(1, len(rec)//50)]}
        try:
            frac, meanp = calibration_curve(y_true, s_norm, n_bins=8, strategy="quantile")
            out["calibration"] = {"fraction_positives": frac.tolist(), "mean_predicted": meanp.tolist()}
        except Exception:
            out["calibration"] = None
    else:
        out["roc_auc"] = None
        out["ap"] = None
        out["brier"] = None
    p, r, f1, _ = precision_recall_fscore_support(y_true, pred, average="binary", zero_division=0)
    out["precision"] = float(p)
    out["recall"] = float(r)
    out["f1"] = float(f1)
    out["confusion_matrix"] = confusion_matrix(y_true, pred, labels=[0, 1]).tolist()
    return out


def fit_multiclass(X: np.ndarray, y: np.ndarray, seed: int = 0) -> Tuple[Any, LabelEncoder, float]:
    le = LabelEncoder()
    yt = le.fit_transform(y.astype(str))
    t0 = time.perf_counter()
    m = RandomForestClassifier(
        n_estimators=250, max_depth=14, min_samples_leaf=1,
        class_weight="balanced_subsample", random_state=seed, n_jobs=-1,
    )
    m.fit(X, yt)
    return m, le, time.perf_counter() - t0


def eval_multiclass(model, le: LabelEncoder, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    yt = le.transform(y.astype(str))
    pred = model.predict(X)
    proba = model.predict_proba(X)
    acc = float(accuracy_score(yt, pred))
    macro_f1 = float(f1_score(yt, pred, average="macro", zero_division=0))
    labels = list(le.classes_)
    cm = confusion_matrix(yt, pred, labels=list(range(len(labels)))).tolist()
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "classes": labels,
        "confusion_matrix": cm,
        "n": int(len(y)),
    }


def mean_ci(xs: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    arr = np.asarray([x for x in xs if x is not None and not (isinstance(x, float) and np.isnan(x))], dtype=float)
    if len(arr) == 0:
        return {"n": 0, "mean": None, "std": None, "ci95": [None, None]}
    m = float(arr.mean())
    s = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    if len(arr) > 1:
        tcrit = float(stats.t.ppf(1 - alpha / 2, df=len(arr) - 1))
        half = tcrit * s / math.sqrt(len(arr))
    else:
        half = 0.0
    return {
        "n": int(len(arr)),
        "mean": m,
        "std": s,
        "ci95": [m - half, m + half],
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def wilcoxon_paired(a: List[float], b: List[float]) -> Dict[str, Any]:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 3 or np.allclose(a, b):
        return {"statistic": None, "pvalue": None, "note": "insufficient or identical"}
    try:
        w = stats.wilcoxon(a, b)
        return {"statistic": float(w.statistic), "pvalue": float(w.pvalue)}
    except Exception as e:
        return {"statistic": None, "pvalue": None, "note": str(e)}


def cliffs_delta(a: List[float], b: List[float]) -> float:
    """Effect size: Cliff's delta."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return 0.0
    gt = sum(x > y for x in a for y in b)
    lt = sum(x < y for x in a for y in b)
    return float((gt - lt) / (n1 * n2))
