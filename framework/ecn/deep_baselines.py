#!/usr/bin/env python3
"""Deep tabular / graph baselines: TabNet and true GraphSAGE (message-passing).

Scientific notes:
- TabNet: pytorch-tabnet on the same telem_only matrices as other tabular baselines.
- GraphSAGE: pure PyTorch inductive GraphSAGE over DigitalTwin device adjacency;
  node features are telemetry (+ optional twin scalars) per (device, time-bin).
  This is NOT the historical LightGBM ``gnn_graphsage_proxy``.
"""
from __future__ import annotations

import time
import warnings
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from ecn.models import FitResult, eval_binary, tune_threshold

HAS_TORCH = False
HAS_TABNET = False
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    HAS_TORCH = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore
    nn = None  # type: ignore
    F = None  # type: ignore

try:
    from pytorch_tabnet.tab_model import TabNetClassifier

    HAS_TABNET = True
except Exception:  # pragma: no cover
    TabNetClassifier = None  # type: ignore


def fit_tabnet(X: np.ndarray, y: np.ndarray, seed: int = 0, X_val: Optional[np.ndarray] = None, y_val: Optional[np.ndarray] = None) -> FitResult:
    """Fit TabNetClassifier; falls back to LightGBM/sklearn GB if unavailable."""
    t0 = time.perf_counter()
    if not HAS_TABNET:
        from ecn.models import fit_binary

        return fit_binary("lightgbm", X, y, seed=seed)

    n_pos = max(int(y.sum()), 1)
    n_neg = max(int(len(y) - y.sum()), 1)
    clf = TabNetClassifier(
        n_d=16,
        n_a=16,
        n_steps=3,
        gamma=1.3,
        n_independent=2,
        n_shared=2,
        seed=seed,
        verbose=0,
        device_name="cpu",
    )
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int64)
    eval_set = None
    eval_name = None
    if X_val is not None and y_val is not None and len(y_val) and len(np.unique(y_val)) > 1:
        eval_set = [(np.asarray(X_val, dtype=np.float32), np.asarray(y_val, dtype=np.int64))]
        eval_name = ["val"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf.fit(
            X,
            y,
            eval_set=eval_set,
            eval_name=eval_name,
            eval_metric=["auc"],
            max_epochs=80,
            patience=12,
            batch_size=min(1024, max(64, len(X))),
            virtual_batch_size=min(128, max(16, len(X) // 4)),
            weights=1,  # auto class balancing inside tabnet when weights=1
            drop_last=False,
        )
    return FitResult(name="tabnet", model=clf, train_time_s=time.perf_counter() - t0, n_features=X.shape[1])


def predict_tabnet(fit: FitResult, X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=np.float32)
    proba = fit.model.predict_proba(X)
    if proba.ndim == 2 and proba.shape[1] >= 2:
        return proba[:, 1].astype(float)
    return proba.reshape(-1).astype(float)


if HAS_TORCH:

    class SAGEConv(nn.Module):
        """Mean-aggregator GraphSAGE convolution (Hamilton et al.)."""

        def __init__(self, in_dim: int, out_dim: int):
            super().__init__()
            self.lin_self = nn.Linear(in_dim, out_dim)
            self.lin_neigh = nn.Linear(in_dim, out_dim)

        def forward(self, x: "torch.Tensor", edge_index: "torch.Tensor") -> "torch.Tensor":
            # edge_index: [2, E] undirected (both directions)
            if edge_index.numel() == 0:
                return F.relu(self.lin_self(x))
            src, dst = edge_index[0], edge_index[1]
            n = x.size(0)
            neigh_sum = torch.zeros_like(x)
            neigh_sum.index_add_(0, dst, x[src])
            deg = torch.zeros(n, device=x.device).index_add_(0, dst, torch.ones(dst.numel(), device=x.device))
            deg = deg.clamp(min=1.0).unsqueeze(-1)
            neigh_mean = neigh_sum / deg
            return F.relu(self.lin_self(x) + self.lin_neigh(neigh_mean))

    class GraphSAGEBinary(nn.Module):
        def __init__(self, in_dim: int, hidden: int = 32, dropout: float = 0.2):
            super().__init__()
            self.conv1 = SAGEConv(in_dim, hidden)
            self.conv2 = SAGEConv(hidden, hidden)
            self.dropout = dropout
            self.out = nn.Linear(hidden, 1)

        def forward(self, x: "torch.Tensor", edge_index: "torch.Tensor") -> "torch.Tensor":
            h = self.conv1(x, edge_index)
            h = F.dropout(h, p=self.dropout, training=self.training)
            h = self.conv2(h, edge_index)
            h = F.dropout(h, p=self.dropout, training=self.training)
            return self.out(h).squeeze(-1)


def _device_index(twin) -> Tuple[List[str], Dict[str, int]]:
    ids = [str(d) for d in twin.devices["device_id"].tolist()]
    return ids, {d: i for i, d in enumerate(ids)}


def _edge_index(twin, idx: Dict[str, int], device: str = "cpu") -> "torch.Tensor":
    rows, cols = [], []
    for a, nbrs in (twin.adjacency or {}).items():
        ia = idx.get(str(a))
        if ia is None:
            continue
        for b in nbrs:
            ib = idx.get(str(b))
            if ib is None:
                continue
            rows.append(ia)
            cols.append(ib)
    if not rows:
        return torch.zeros((2, 0), dtype=torch.long, device=device)
    return torch.tensor([rows, cols], dtype=torch.long, device=device)


def _bin_node_matrix(
    df: pd.DataFrame,
    feat_bin: Any,
    device_ids: Sequence[str],
    idx: Dict[str, int],
    feature_cols: Sequence[str],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return X [N,F], y [N], mask [N] for one time bin (mask=1 if labeled row exists)."""
    n = len(device_ids)
    f = len(feature_cols)
    X = np.zeros((n, f), dtype=np.float32)
    y = np.zeros(n, dtype=np.float32)
    mask = np.zeros(n, dtype=bool)
    sub = df.loc[df["feat_bin"] == feat_bin]
    for _, row in sub.iterrows():
        eid = str(row["entity_id"])
        j = idx.get(eid)
        if j is None:
            continue
        X[j] = row[list(feature_cols)].astype(float).values
        y[j] = float(row["y"])
        mask[j] = True
    return X, y, mask


def eval_graphsage(
    df: pd.DataFrame,
    twin,
    feature_cols: List[str],
    seed: int = 0,
    epochs: int = 40,
    hidden: int = 32,
    lr: float = 1e-2,
) -> Dict[str, Any]:
    """Train/eval true GraphSAGE on DigitalTwin adjacency over temporal device bins."""
    if not HAS_TORCH:
        return {"error": "torch_unavailable", "method": "graphsage", "features_mode": "graph_telem"}
    if "entity_id" not in df.columns or "feat_bin" not in df.columns:
        return {"error": "missing_entity_or_bin", "method": "graphsage"}
    if not feature_cols:
        return {"error": "no_features", "method": "graphsage"}

    device_ids, idx = _device_index(twin)
    device = "cpu"
    edge_index = _edge_index(twin, idx, device=device)
    torch.manual_seed(seed)
    np.random.seed(seed)

    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]
    train_bins = sorted(train_df["feat_bin"].unique().tolist())
    val_bins = sorted(val_df["feat_bin"].unique().tolist())
    test_bins = sorted(test_df["feat_bin"].unique().tolist())
    if not train_bins or not test_bins:
        return {"error": "empty_bins", "method": "graphsage"}

    in_dim = len(feature_cols)
    model = GraphSAGEBinary(in_dim, hidden=hidden).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    # class imbalance from train labels
    y_all = train_df["y"].astype(float).values
    n_pos = max(float(y_all.sum()), 1.0)
    n_neg = max(float(len(y_all) - y_all.sum()), 1.0)
    pos_weight = torch.tensor([n_neg / n_pos], dtype=torch.float32, device=device)

    t0 = time.perf_counter()
    model.train()
    for ep in range(epochs):
        total_loss = 0.0
        n_graphs = 0
        rng = np.random.default_rng(seed + ep)
        order = list(train_bins)
        rng.shuffle(order)
        for b in order[: min(64, len(order))]:  # subsample bins/epoch for speed
            X, y, mask = _bin_node_matrix(train_df, b, device_ids, idx, feature_cols)
            if not mask.any() or y[mask].sum() == 0 and (1 - y[mask]).sum() == 0:
                continue
            xt = torch.tensor(X, dtype=torch.float32, device=device)
            yt = torch.tensor(y, dtype=torch.float32, device=device)
            mt = torch.tensor(mask, dtype=torch.bool, device=device)
            opt.zero_grad()
            logits = model(xt, edge_index)
            loss = F.binary_cross_entropy_with_logits(logits[mt], yt[mt], pos_weight=pos_weight)
            loss.backward()
            opt.step()
            total_loss += float(loss.item())
            n_graphs += 1
        if (ep + 1) % 10 == 0 and n_graphs:
            # light val monitoring (no early stop required for fairness/simplicity)
            model.eval()
            with torch.no_grad():
                val_scores, val_y = [], []
                for b in val_bins[:32]:
                    X, y, mask = _bin_node_matrix(val_df, b, device_ids, idx, feature_cols)
                    if not mask.any():
                        continue
                    xt = torch.tensor(X, dtype=torch.float32, device=device)
                    logits = model(xt, edge_index)
                    prob = torch.sigmoid(logits).cpu().numpy()
                    val_scores.extend(prob[mask].tolist())
                    val_y.extend(y[mask].tolist())
            model.train()
    train_t = time.perf_counter() - t0

    def score_split(split_df: pd.DataFrame, bins: List[Any]) -> Tuple[np.ndarray, np.ndarray]:
        model.eval()
        scores, labels = [], []
        with torch.no_grad():
            for b in bins:
                X, y, mask = _bin_node_matrix(split_df, b, device_ids, idx, feature_cols)
                if not mask.any():
                    continue
                xt = torch.tensor(X, dtype=torch.float32, device=device)
                logits = model(xt, edge_index)
                prob = torch.sigmoid(logits).cpu().numpy()
                scores.extend(prob[mask].tolist())
                labels.extend(y[mask].tolist())
        return np.asarray(scores, dtype=float), np.asarray(labels, dtype=int)

    s_va, y_va = score_split(val_df, val_bins) if len(val_df) else (np.array([0.5]), np.array([0]))
    thr = tune_threshold(y_va, s_va) if len(y_va) and len(np.unique(y_va)) > 1 else 0.5
    s_te, y_te = score_split(test_df, test_bins)
    if len(y_te) == 0:
        return {"error": "empty_test_scores", "method": "graphsage", "train_time_s": train_t}

    metrics = eval_binary(y_te, s_te, thr)
    metrics.update(
        {
            "train_time_s": train_t,
            "wall_time_s": train_t,
            "n_features": len(feature_cols),
            "n_train": int(len(train_df)),
            "n_val": int(len(val_df)),
            "n_test": int(len(test_df)),
            "n_devices": len(device_ids),
            "n_edges": int(edge_index.size(1)),
            "features_mode": "graph_telem",
            "method": "graphsage",
            "model_family": "true_graphsage_mean",
            "backend": "pytorch_pure",
            "epochs": epochs,
            "hidden": hidden,
        }
    )
    return metrics


def default_gnn_feature_cols(cols: Sequence[str]) -> List[str]:
    """Telemetry (+ light twin scalars) used as GraphSAGE node features."""
    telem = {
        "cpu_mean",
        "cpu_max",
        "mem_mean",
        "n_polls",
        "err_sum",
        "disc_sum",
        "car_sum",
        "d_cpu_mean",
        "d_cpu_max",
        "d_mem_mean",
        "cpu_z",
        "mem_z",
    }
    twin_light = {"twin_degree", "twin_n_neighbors"}
    use = [c for c in cols if c in telem or c in twin_light]
    if len(use) < 3:
        use = [c for c in cols if not str(c).startswith("cat_")][:12]
    return use
