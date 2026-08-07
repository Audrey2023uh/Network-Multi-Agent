#!/usr/bin/env python3
"""Validate dashboard JSON against manuscript_ready_numbers and topology counts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parents[1] / "public" / "data"
MS = ROOT / "results" / "manuscript_ready_numbers.json"


def main() -> int:
    ms = json.loads(MS.read_text(encoding="utf-8"))
    agg = json.loads((DATA / "aggregate.json").read_text(encoding="utf-8"))
    idx = json.loads((DATA / "index.json").read_text(encoding="utf-8"))

    expected = ms["T1_final_proposed"]["auprc_mean"]
    got = agg["manuscript_ready"]["T1_final_proposed"]["auprc_mean"]
    assert abs(expected - got) < 1e-15, (expected, got)

    final_model = next(m for m in agg["models"] if m["id"] == "ecn_v3_final")
    assert abs(final_model["T1_auprc"]["mean"] - expected) < 1e-15

    # no hard-coded scientific literals in src (heuristic: manuscript digits)
    src = ROOT / "interactive_dashboard" / "src"
    needle = "0.11522078115707056"
    hits = []
    for p in src.rglob("*.{ts,tsx}"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if needle in text:
            hits.append(str(p))
    # also check without brace glob
    hits = []
    for p in list(src.rglob("*.ts")) + list(src.rglob("*.tsx")):
        if needle in p.read_text(encoding="utf-8", errors="ignore"):
            hits.append(str(p.relative_to(ROOT)))
    assert not hits, f"Hard-coded manuscript AUPRC in frontend: {hits}"

    for s in idx["seeds"]:
        topo = json.loads((DATA / f"topology_{s['id']}.json").read_text(encoding="utf-8"))
        assert topo["n_devices"] == s["n_devices"] == len(topo["devices"])
        assert topo["n_links"] == s["n_links"]
        assert topo["n_devices"] == 19 and topo["n_links"] == 31, (s["id"], topo["n_devices"], topo["n_links"])
        # link endpoints resolved
        linked = [l for l in topo["links"] if l.get("_source") and l.get("_target")]
        assert len(linked) == topo["n_links"], s["id"]

    # seed101 AP matches per_seed file
    per = json.loads((ROOT / "results" / "per_seed" / "seed101.json").read_text(encoding="utf-8"))
    dash = json.loads((DATA / "metrics_seed101.json").read_text(encoding="utf-8"))
    src_ap = per["tasks"]["T1_anomaly"]["ecn_proposed__full"]["ap"]
    dash_ap = dash["T1"]["ecn_proposed__full"]["ap"]
    assert abs(src_ap - dash_ap) < 1e-15, (src_ap, dash_ap)

    t2 = agg["manuscript_ready"].get("T2_recommended", {})
    assert t2.get("auprc_mean") is not None, "T2_recommended missing from aggregate"

    print("OK: manuscript AUPRC match, no hard-coded final AUPRC in src, topology 19/31, seed101 AP match, T2 present")
    print("  T1 AUPRC =", expected)
    print("  T2 AUPRC =", t2["auprc_mean"], " source=", t2.get("source"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("VALIDATION FAILED:", e, file=sys.stderr)
        raise SystemExit(1)
