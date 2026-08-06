"""Deterministic helpers for ECNetBench generation."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace


def did(seed: int, *parts: Any) -> str:
    """Deterministic UUIDv5 from seed + parts (reproducible primary keys)."""
    key = "|".join([str(seed)] + [str(p) for p in parts])
    return str(uuid.uuid5(NS, key))


def sha16(*parts: Any) -> str:
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return h[:16]


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    return utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def daterange(start: datetime, end: datetime, step_s: int):
    t = start
    while t <= end:
        yield t
        t += timedelta(seconds=step_s)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))
