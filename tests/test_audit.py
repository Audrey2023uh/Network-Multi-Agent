"""Audit and unit tests for ECNetBench + ECN framework (no dataset mutation)."""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "framework"))
sys.path.insert(0, str(ROOT / "evaluation"))

from ecn.features import temporal_masks  # noqa: E402
from ecn.twin import DigitalTwin  # noqa: E402
import pandas as pd  # noqa: E402

DB = ROOT / "benchmark" / "instances" / "v1" / "ecnetbench_v1.sqlite"
PROHIBITED = re.compile(
    r"\bcursor\b|\bchatgpt\b|\bgpt-|\bopenai\b|\bclaude\b|coding assistant|homework|assignment|course project|student submission",
    re.I,
)
LEAKAGE_FEATURE_DENY = {"incident_id", "y_anomaly_gt", "y_fail_gt", "description"}


@pytest.mark.skipif(not DB.exists(), reason="benchmark sqlite missing")
def test_sqlite_readonly_and_labels():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("label_anomaly_window", "label_failure_horizon", "device", "link", "device_resource_sample"):
        assert t in tables
    con.close()


@pytest.mark.skipif(not DB.exists(), reason="benchmark sqlite missing")
def test_digital_twin_graph():
    twin = DigitalTwin.load(DB)
    assert len(twin.devices) > 0
    assert len(twin.links) > 0
    did = twin.devices["device_id"].iloc[0]
    sf = twin.structural_features(did)
    assert "twin_degree" in sf


def test_temporal_masks_disjoint():
    times = pd.to_datetime(pd.date_range("2025-01-01", periods=100, freq="h", tz="UTC"))
    tr, va, te = temporal_masks(pd.Series(times))
    assert tr.sum() > 0 and va.sum() > 0 and te.sum() > 0
    assert not (tr & va).any() and not (tr & te).any() and not (va & te).any()
    # 70/15/15 approximately
    assert 0.60 < tr.mean() < 0.80
    assert 0.08 < va.mean() < 0.25


@pytest.mark.skipif(not DB.exists(), reason="benchmark sqlite missing")
def test_anomaly_features_no_leakage_cols_and_past_bin():
    from ecn.features import build_anomaly_dataset

    twin = DigitalTwin.load(DB)
    df, cols = build_anomaly_dataset(twin)
    assert not (set(cols) & LEAKAGE_FEATURE_DENY)
    assert "incident_id" not in cols
    # feat_bin is strictly before t_start
    assert (df["feat_bin"] < df["t_start"]).all()
    assert set(df["split"]) == {"train", "val", "test"}


def test_no_absolute_windows_paths_in_evaluation_script():
    text = (ROOT / "evaluation" / "run_full_evaluation.py").read_text(encoding="utf-8")
    assert "C:\\Users" not in text
    assert "OneDrive" not in text


def test_no_prohibited_wording_in_reports():
    for path in (ROOT / "docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not PROHIBITED.search(text), f"prohibited wording in {path}"
    for path in (ROOT / "reports").rglob("*.md"):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not PROHIBITED.search(text), f"prohibited wording in {path}"


def test_fusion_nesting_property_unit():
    """Anchored fusion weights for telem_only must be one-hot on telem_lr."""
    from ecn.models import ECNFusionModel

    rng = np.random.default_rng(0)
    n, d = 200, 8
    X = rng.normal(size=(n, d))
    # rare positives correlated with col0
    y = (X[:, 0] > 1.2).astype(int)
    names = ["cpu_mean", "cpu_max", "mem_mean", "err_sum", "twin_degree", "twin_nbr_mean", "twin_is_core", "cpu_z"]
    # force enough val positives
    Xtr, ytr = X[:140], y[:140]
    Xva, yva = X[140:170], y[140:170]
    Xte, yte = X[170:], y[170:]
    if yva.sum() == 0:
        yva[0] = 1
    model = ECNFusionModel(seed=0).fit(Xtr, ytr, Xva, yva, names)
    assert model.fusion_w is not None
    assert abs(model.fusion_w.sum() - 1.0) < 1e-6
    assert model.fusion_w[0] >= 0.5 - 1e-9  # telem anchored or telem_only


def test_seed_list_complete():
    from run_full_evaluation import SEEDS

    names = [s[0] for s in SEEDS]
    assert names == ["v1.1.0-INST", "seed101", "seed202", "seed303", "seed404", "seed505"]
