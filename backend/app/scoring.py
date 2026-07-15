"""Evidence → confidence scoring. Pure functions, no I/O — unit-tested.

An edge's confidence rises with the number and strength of supporting sources,
their recency, and agreement; it falls when the Skeptic finds contradictions.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.graph.models import Evidence, Stance

# Year used for recency decay; injectable for deterministic tests.
_CURRENT_YEAR = datetime.now(UTC).year


def _recency_factor(year: int | None, current_year: int = _CURRENT_YEAR) -> float:
    """1.0 for current-year evidence, decaying ~0.03/yr, floored at 0.5."""
    if year is None:
        return 0.8
    age = max(0, current_year - year)
    return max(0.5, 1.0 - 0.03 * age)


def aggregate_confidence(evidence: list[Evidence], current_year: int = _CURRENT_YEAR) -> float:
    """Combine evidence items into a single confidence in [0, 1].

    Supporting items accumulate via a diminishing-returns (noisy-OR-style) rule so
    more independent sources always help but never exceed 1. Contradictions apply
    a multiplicative penalty. Deduped upstream by ``Evidence.dedup_key``.
    """
    if not evidence:
        return 0.0

    support_miss = 1.0  # product of (1 - weighted_support); 1.0 == no support yet
    contra_miss = 1.0  # product of (1 - weighted_contradiction)
    for ev in evidence:
        w = max(0.0, min(1.0, ev.weight)) * _recency_factor(ev.recency_year, current_year)
        if ev.stance is Stance.SUPPORTS:
            support_miss *= 1.0 - w
        else:
            contra_miss *= 1.0 - w

    support = 1.0 - support_miss  # noisy-OR over supporting evidence
    contradiction = 1.0 - contra_miss
    confidence = support * (1.0 - 0.7 * contradiction)  # skeptic caps, never zeroes
    return round(max(0.0, min(1.0, confidence)), 3)


def dedup_evidence(evidence: list[Evidence]) -> list[Evidence]:
    """Keep the strongest item per (source, stance) — the idempotency guarantee."""
    best: dict[str, Evidence] = {}
    for ev in evidence:
        cur = best.get(ev.dedup_key)
        if cur is None or ev.weight > cur.weight:
            best[ev.dedup_key] = ev
    return list(best.values())
