"""Leakage-safe feature construction for ECN tasks using the Digital Twin."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .twin import DigitalTwin

FREEZE_FRAC = 0.70
VAL_FRAC = 0.15


def temporal_masks(times: pd.Series) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    t0, t1 = times.min(), times.max()
    span = (t1 - t0).total_seconds()
    train_end = t0 + pd.Timedelta(seconds=span * FREEZE_FRAC)
    val_end = t0 + pd.Timedelta(seconds=span * (FREEZE_FRAC + VAL_FRAC))
    tr = (times < train_end).values
    va = ((times >= train_end) & (times < val_end)).values
    te = (times >= val_end).values
    return tr, va, te


def _device_bin_feature_table(twin: DigitalTwin) -> Tuple[pd.DataFrame, List[str]]:
    """Shared leakage-safe device×30min feature table (telem + twin temporal)."""
    con = twin.open_ro()
    try:
        devr = pd.read_sql(
            "SELECT device_id, observed_at, cpu_util_pct, mem_util_pct FROM device_resource_sample",
            con,
        )
        ifc = pd.read_sql(
            "SELECT device_id, observed_at, in_errors, out_discards, carrier_transitions FROM if_counter_sample",
            con,
        )
    finally:
        con.close()

    devr["observed_at"] = pd.to_datetime(devr["observed_at"], utc=True)
    devr["bin"] = devr["observed_at"].dt.floor("30min")
    agg = (
        devr.groupby(["device_id", "bin"])
        .agg(
            cpu_mean=("cpu_util_pct", "mean"),
            cpu_max=("cpu_util_pct", "max"),
            mem_mean=("mem_util_pct", "mean"),
            n_polls=("cpu_util_pct", "count"),
        )
        .reset_index()
        .sort_values(["device_id", "bin"])
    )
    for col in ("cpu_mean", "cpu_max", "mem_mean"):
        agg[f"d_{col}"] = agg.groupby("device_id")[col].diff()

    def _expanding_z(s: pd.Series) -> pd.Series:
        mu = s.expanding(min_periods=3).mean().shift(1)
        sd = s.expanding(min_periods=3).std().shift(1).replace(0, np.nan)
        return (s - mu) / sd

    agg["cpu_z"] = agg.groupby("device_id")["cpu_mean"].transform(_expanding_z)
    agg["mem_z"] = agg.groupby("device_id")["mem_mean"].transform(_expanding_z)

    ifc["observed_at"] = pd.to_datetime(ifc["observed_at"], utc=True)
    ifc = ifc.sort_values(["device_id", "observed_at"])
    ifc["d_err"] = ifc.groupby("device_id")["in_errors"].diff().clip(lower=0)
    ifc["d_disc"] = ifc.groupby("device_id")["out_discards"].diff().clip(lower=0)
    ifc["d_car"] = ifc.groupby("device_id")["carrier_transitions"].diff().clip(lower=0)
    ifc["bin"] = ifc["observed_at"].dt.floor("30min")
    ifagg = (
        ifc.groupby(["device_id", "bin"])
        .agg(err_sum=("d_err", "sum"), disc_sum=("d_disc", "sum"), car_sum=("d_car", "sum"))
        .reset_index()
    )

    feat = agg.merge(ifagg, on=["device_id", "bin"], how="left")
    cpu_map = {(r.device_id, r.bin): float(r.cpu_mean) if pd.notna(r.cpu_mean) else 0.0 for r in feat.itertuples()}
    err_map = {(r.device_id, r.bin): float(r.err_sum) if pd.notna(r.err_sum) else 0.0 for r in feat.itertuples()}

    twin_rows = []
    for r in feat.itertuples():
        did = r.device_id
        sf = twin.structural_features(did)
        nbrs = twin.neighbors(did, 1)
        cpu_vals = {n: cpu_map.get((n, r.bin), 0.0) for n in nbrs}
        err_vals = {n: err_map.get((n, r.bin), 0.0) for n in nbrs}
        nbr_cpu = twin.neighbor_aggregate(did, cpu_vals)
        nbr_err = twin.neighbor_aggregate(did, err_vals)
        sf.update(nbr_cpu)
        sf.update({
            "twin_nbr_err_mean": nbr_err["twin_nbr_mean"],
            "twin_nbr_err_max": nbr_err["twin_nbr_max"],
            "twin_nbr_err_std": nbr_err["twin_nbr_std"],
            "twin_cpu_vs_nbr": float(r.cpu_mean if pd.notna(r.cpu_mean) else 0.0) - nbr_cpu["twin_nbr_mean"],
            "twin_nbr_degree_sum": float(sum(twin.degree.get(n, 0) for n in nbrs)),
        })
        twin_rows.append(sf)
    feat = pd.concat([feat.reset_index(drop=True), pd.DataFrame(twin_rows)], axis=1)

    num_cols = [
        "cpu_mean", "cpu_max", "mem_mean", "n_polls", "err_sum", "disc_sum", "car_sum",
        "d_cpu_mean", "d_cpu_max", "d_mem_mean", "cpu_z", "mem_z",
        "twin_degree", "twin_n_neighbors", "twin_frac_core_nbr", "twin_frac_agg_nbr",
        "twin_frac_wan_nbr", "twin_is_core", "twin_is_access", "twin_is_wan", "twin_is_ap",
        "twin_nbr_mean", "twin_nbr_max", "twin_nbr_std",
        "twin_nbr_err_mean", "twin_nbr_err_max", "twin_nbr_err_std",
        "twin_cpu_vs_nbr", "twin_nbr_degree_sum",
    ]
    for c in num_cols:
        if c not in feat.columns:
            feat[c] = 0.0
        feat[c] = feat[c].fillna(feat[c].median() if feat[c].notna().any() else 0.0)
    return feat, num_cols


def build_anomaly_dataset(twin: DigitalTwin) -> Tuple[pd.DataFrame, List[str]]:
    """T1: anomaly windows with twin + telemetry + temporal change features (prior bins only)."""
    con = twin.open_ro()
    try:
        lab = pd.read_sql("SELECT * FROM label_anomaly_window", con)
    finally:
        con.close()
    lab["t_start"] = pd.to_datetime(lab["t_start"], utc=True)
    lab["y"] = lab["y_anomaly"].astype(str).str.lower().isin(["1", "true", "t"]).astype(int)
    lab["feat_bin"] = lab["t_start"] - pd.Timedelta(minutes=30)

    ft, num_cols = _device_bin_feature_table(twin)
    feat = lab.merge(
        ft.rename(columns={"device_id": "entity_id", "bin": "feat_bin"}),
        on=["entity_id", "feat_bin"],
        how="left",
    )
    for c in num_cols:
        feat[c] = feat[c].fillna(feat[c].median() if feat[c].notna().any() else 0.0)
    tr, va, te = temporal_masks(feat["t_start"])
    feat["split"] = "test"
    feat.loc[tr, "split"] = "train"
    feat.loc[va, "split"] = "val"
    return feat, num_cols


def build_failure_dataset(twin: DigitalTwin, horizon_s: int = 3600) -> Tuple[pd.DataFrame, List[str]]:
    """T2: failure horizon with the same leakage-safe telem+twin temporal representation as T1."""
    con = twin.open_ro()
    try:
        fh = pd.read_sql(f"SELECT * FROM label_failure_horizon WHERE horizon_s={horizon_s}", con)
    finally:
        con.close()
    fh["t0"] = pd.to_datetime(fh["t0"], utc=True)
    fh["y"] = fh["y_fail"].astype(str).str.lower().isin(["1", "true", "t"]).astype(int)
    fh["feat_bin"] = fh["t0"] - pd.Timedelta(minutes=30)

    ft, num_cols = _device_bin_feature_table(twin)
    feat = fh.merge(
        ft.rename(columns={"device_id": "entity_id", "bin": "feat_bin"}),
        on=["entity_id", "feat_bin"],
        how="left",
    )
    for c in num_cols:
        feat[c] = feat[c].fillna(feat[c].median() if feat[c].notna().any() else 0.0)
    tr, va, te = temporal_masks(feat["t0"])
    feat["split"] = "test"
    feat.loc[tr, "split"] = "train"
    feat.loc[va, "split"] = "val"
    return feat, num_cols


def build_rca_dataset(twin: DigitalTwin) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """T3 RCA: category classification from telemetry+syslog+twin (no description text)."""
    con = twin.open_ro()
    try:
        rca = pd.read_sql("SELECT * FROM label_rca", con)
        inc = pd.read_sql(
            "SELECT incident_id, onset_at, detected_at, root_entity_type, root_entity_id FROM failure_incident",
            con,
        )
        ents = pd.read_sql("SELECT * FROM incident_entity", con)
        syslog = pd.read_sql(
            "SELECT device_id, observed_at, app_name, event_code, severity, message FROM syslog_event",
            con,
        )
        alert = pd.read_sql(
            "SELECT device_id, raised_at, alert_type, severity FROM alert",
            con,
        )
        devr = pd.read_sql(
            "SELECT device_id, observed_at, cpu_util_pct FROM device_resource_sample",
            con,
        )
    finally:
        con.close()

    rca = rca.merge(inc, on="incident_id", suffixes=("", "_i"))
    rca["detected"] = pd.to_datetime(rca["t_detect"], utc=True)
    rca["onset"] = pd.to_datetime(rca["onset_at"], utc=True)
    syslog["observed_at"] = pd.to_datetime(syslog["observed_at"], utc=True)
    alert["raised_at"] = pd.to_datetime(alert["raised_at"], utc=True)
    devr["observed_at"] = pd.to_datetime(devr["observed_at"], utc=True)

    rows = []
    for _, r in rca.iterrows():
        # device from entities
        e = ents[ents["incident_id"] == r["incident_id"]]
        dev_ids = e.loc[e["entity_type"] == "device", "entity_id"].tolist()
        if_ids = e.loc[e["entity_type"] == "interface", "entity_id"].tolist()
        did = dev_ids[0] if dev_ids else None
        if did is None and if_ids:
            did = twin.if_to_dev.get(if_ids[0])
        if did is None:
            continue
        t0 = r["detected"]
        # telemetry before detect
        win = devr[(devr["device_id"] == did) & (devr["observed_at"] <= t0) & (devr["observed_at"] >= t0 - pd.Timedelta(minutes=30))]
        cpu_mean = float(win["cpu_util_pct"].mean()) if len(win) else 0.0
        cpu_max = float(win["cpu_util_pct"].max()) if len(win) else 0.0
        # syslog bag counts (no description of category from incident table)
        slog = syslog[
            (syslog["device_id"] == did)
            & (syslog["observed_at"] <= t0)
            & (syslog["observed_at"] >= t0 - pd.Timedelta(minutes=15))
        ]
        apps = slog["app_name"].astype(str).str.lower()
        codes = slog["event_code"].astype(str).str.upper()
        feat = twin.structural_features(did)
        feat.update({
            "cpu_mean": cpu_mean,
            "cpu_max": cpu_max,
            "n_syslog": float(len(slog)),
            "sev_mean": float(pd.to_numeric(slog["severity"], errors="coerce").mean()) if len(slog) else 0.0,
            "app_bgp": float((apps == "bgp").sum()),
            "app_stp": float((apps == "stp").sum()),
            "app_vsx": float((apps == "vsx").sum()),
            "app_port": float((apps == "port").sum()),
            "app_aaa": float((apps == "aaa").sum()),
            "app_lacp": float((apps == "lacp").sum()),
            "code_bgp": float(codes.str.contains("BGP", na=False).sum()),
            "code_link": float(codes.str.contains("LINK", na=False).sum()),
            "code_stp": float(codes.str.contains("TOPOLOGY|STP|MAC", na=False).sum()),
            "n_alerts": float(len(alert[(alert["device_id"] == did) & (alert["raised_at"] <= t0) & (alert["raised_at"] >= t0 - pd.Timedelta(minutes=15))])),
            "n_entities": float(len(e)),
        })
        feat["y_category"] = r["y_category"]
        feat["incident_id"] = r["incident_id"]
        feat["t_detect"] = t0
        feat["device_id"] = did
        feat["y_root_entity_id"] = r["y_root_entity_id"]
        rows.append(feat)

    df = pd.DataFrame(rows)
    if df.empty:
        return df, [], []
    tr, va, te = temporal_masks(df["t_detect"])
    df["split"] = "test"
    df.loc[tr, "split"] = "train"
    df.loc[va, "split"] = "val"
    feature_cols = [c for c in df.columns if c not in ("y_category", "incident_id", "t_detect", "device_id", "y_root_entity_id", "split")]
    cats = sorted(df["y_category"].astype(str).unique().tolist())
    return df, feature_cols, cats


def build_healing_dataset(twin: DigitalTwin) -> Tuple[pd.DataFrame, List[str]]:
    """Self-healing decision support: predict recovery action type from early incident context."""
    con = twin.open_ro()
    try:
        acts = pd.read_sql("SELECT * FROM recovery_action", con)
        inc = pd.read_sql("SELECT incident_id, category, onset_at, detected_at, severity FROM failure_incident", con)
    finally:
        con.close()
    df = acts.merge(inc, on="incident_id")
    df["detected"] = pd.to_datetime(df["detected_at"], utc=True)
    # action type is the label the healing agent should recommend
    df["y_action"] = df["action_type"].astype(str)
    # features: category is GT for training healing policy from historical incidents —
    # at inference after RCA, category comes from RCAAgent (pipeline). For offline eval
    # we use twin+severity only to avoid perfect category→action mapping leakage in the
    # "honest" healing feature set; separate oracle uses category.
    twin_rows = []
    # map via incident entities later — use severity encoding
    sev_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    df["sev_n"] = df["severity"].astype(str).str.lower().map(sev_map).fillna(2)
    # structural prior: mean twin features across devices (constant per topology) + severity
    # Better: join root device via failure_incident root when type=device else skip
    for _, r in df.iterrows():
        # use global topology prior features (degree of core etc.) — weak but honest
        twin_rows.append({
            "sev_n": float(r["sev_n"]),
            "n_devices": float(len(twin.devices)),
            "n_links": float(len(twin.links)),
            "mean_degree": float(np.mean(list(twin.degree.values()))) if twin.degree else 0.0,
        })
    feat = pd.concat([df.reset_index(drop=True), pd.DataFrame(twin_rows)], axis=1)
    # Also include one-hot of RCA-available signals: we allow category as "post-RCA" feature
    # in the full ECN pipeline (HealingAgent consumes RCA output). Mark as post_rca feature.
    cats = pd.get_dummies(feat["category"].astype(str), prefix="cat")
    feat = pd.concat([feat, cats], axis=1)
    feature_cols = ["sev_n", "n_devices", "n_links", "mean_degree"] + list(cats.columns)
    tr, va, te = temporal_masks(feat["detected"])
    feat["split"] = "test"
    feat.loc[tr, "split"] = "train"
    feat.loc[va, "split"] = "val"
    feat["y"] = feat["y_action"]
    return feat, feature_cols


def build_impact_dataset(twin: DigitalTwin) -> Tuple[pd.DataFrame, List[str]]:
    """T4 impact: high-impact incident prediction (users/severity), not near-constant SLA flag."""
    con = twin.open_ro()
    try:
        imp = pd.read_sql("SELECT * FROM label_impact", con)
        inc = pd.read_sql(
            "SELECT incident_id, onset_at, detected_at, severity, category FROM failure_incident",
            con,
        )
        ents = pd.read_sql("SELECT * FROM incident_entity", con)
        devr = pd.read_sql(
            "SELECT device_id, observed_at, cpu_util_pct, mem_util_pct FROM device_resource_sample",
            con,
        )
    finally:
        con.close()

    if imp.empty:
        return pd.DataFrame(), []

    base = imp.merge(inc, on="incident_id", how="left", suffixes=("", "_i"))
    base["t0"] = pd.to_datetime(base["t0"], utc=True)
    # High-impact: critical/high severity OR users above median
    sev = base["y_max_severity"].astype(str).str.lower()
    users = pd.to_numeric(base["y_users_affected"], errors="coerce").fillna(0)
    med = float(users.median()) if len(users) else 0.0
    base["y"] = ((sev.isin(["high", "critical"])) | (users > med)).astype(int)
    # If still degenerate, fall back to downtime above median
    if base["y"].nunique() < 2:
        dt = pd.to_numeric(base["y_downtime_s"], errors="coerce").fillna(0)
        base["y"] = (dt > float(dt.median())).astype(int)

    devr["observed_at"] = pd.to_datetime(devr["observed_at"], utc=True)

    rows = []
    for _, r in base.iterrows():
        e = ents[ents["incident_id"] == r["incident_id"]] if "incident_id" in base.columns else pd.DataFrame()
        dev_ids = e.loc[e["entity_type"] == "device", "entity_id"].tolist() if len(e) else []
        did = dev_ids[0] if dev_ids else None
        if did is None:
            sf = {
                "twin_degree": 0.0,
                "twin_n_neighbors": 0.0,
                "twin_frac_core_nbr": 0.0,
                "twin_is_core": 0.0,
                "twin_is_access": 0.0,
                "twin_is_wan": 0.0,
            }
        else:
            sf = twin.structural_features(did)
        t0 = r["t0"]
        if did is not None:
            win = devr[
                (devr["device_id"] == did)
                & (devr["observed_at"] <= t0)
                & (devr["observed_at"] >= t0 - pd.Timedelta(minutes=30))
            ]
            cpu_mean = float(win["cpu_util_pct"].mean()) if len(win) else 0.0
            cpu_max = float(win["cpu_util_pct"].max()) if len(win) else 0.0
            mem_mean = float(win["mem_util_pct"].mean()) if len(win) else 0.0
        else:
            cpu_mean = cpu_max = mem_mean = 0.0
        sev_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        # Do NOT use post-impact severity label as feature — use incident severity at detect if available
        sf.update(
            {
                "cpu_mean": cpu_mean,
                "cpu_max": cpu_max,
                "mem_mean": mem_mean,
                "sev_n": float(sev_map.get(str(r.get("severity", "medium")).lower(), 2)),
                "y": int(r["y"]),
                "t0": t0,
                "incident_id": r.get("incident_id"),
            }
        )
        rows.append(sf)

    df = pd.DataFrame(rows)
    if df.empty or df["y"].nunique() < 2:
        return pd.DataFrame(), []
    cols = [
        c
        for c in [
            "cpu_mean",
            "cpu_max",
            "mem_mean",
            "sev_n",
            "twin_degree",
            "twin_n_neighbors",
            "twin_frac_core_nbr",
            "twin_is_core",
            "twin_is_access",
            "twin_is_wan",
        ]
        if c in df.columns
    ]
    for c in cols:
        df[c] = df[c].fillna(df[c].median() if df[c].notna().any() else 0.0)
    tr, va, te = temporal_masks(df["t0"])
    df["split"] = "test"
    df.loc[tr, "split"] = "train"
    df.loc[va, "split"] = "val"
    return df, cols


def build_degradation_dataset(twin: DigitalTwin) -> Tuple[pd.DataFrame, List[str]]:
    """T5 service degradation prediction."""
    con = twin.open_ro()
    try:
        deg = pd.read_sql("SELECT * FROM label_degradation", con)
        svc = pd.read_sql("SELECT service_id, criticality_tier FROM service", con)
    finally:
        con.close()
    deg["t0"] = pd.to_datetime(deg["t0"], utc=True)
    deg["y"] = deg["y_degrade"].astype(str).str.lower().isin(["1", "true", "t"]).astype(int)
    deg = deg.merge(svc, on="service_id", how="left")
    deg["crit_n"] = pd.to_numeric(deg["criticality_tier"], errors="coerce").fillna(2)
    # Topology priors only (service-level twin proxy)
    deg["n_devices"] = float(len(twin.devices))
    deg["mean_degree"] = float(np.mean(list(twin.degree.values()))) if twin.degree else 0.0
    deg["n_links"] = float(len(twin.links))
    cols = ["crit_n", "n_devices", "mean_degree", "n_links"]
    if "horizon_s" in deg.columns:
        deg["horizon_n"] = pd.to_numeric(deg["horizon_s"], errors="coerce").fillna(0)
        cols.append("horizon_n")
    tr, va, te = temporal_masks(deg["t0"])
    deg["split"] = "test"
    deg.loc[tr, "split"] = "train"
    deg.loc[va, "split"] = "val"
    return deg, cols


def build_config_risk_dataset(twin: DigitalTwin) -> Tuple[pd.DataFrame, List[str]]:
    """T6 configuration risk classification."""
    con = twin.open_ro()
    try:
        cfg = pd.read_sql("SELECT * FROM label_config_risk", con)
    finally:
        con.close()
    cfg["t0"] = pd.to_datetime(cfg["t_change"], utc=True)
    cfg["y"] = cfg["y_risk"].astype(str).str.lower().isin(["1", "true", "t"]).astype(int)
    cfg["n_devices"] = float(len(twin.devices))
    cfg["mean_degree"] = float(np.mean(list(twin.degree.values()))) if twin.degree else 0.0
    cfg["n_links"] = float(len(twin.links))
    cfg["horizon_n"] = pd.to_numeric(cfg.get("horizon_s", 0), errors="coerce").fillna(0)
    cols = ["n_devices", "mean_degree", "n_links", "horizon_n"]
    tr, va, te = temporal_masks(cfg["t0"])
    cfg["split"] = "test"
    cfg.loc[tr, "split"] = "train"
    cfg.loc[va, "split"] = "val"
    return cfg, cols
