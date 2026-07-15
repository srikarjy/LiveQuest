"""Scoring is pure — these run everywhere, no database needed."""

from __future__ import annotations

from app.graph.models import Evidence, Provenance, Stance
from app.scoring import aggregate_confidence, dedup_evidence

YEAR = 2026


def ev(
    source_id: str,
    stance: Stance = Stance.SUPPORTS,
    weight: float = 0.5,
    year: int = YEAR,
) -> Evidence:
    return Evidence(
        provenance=Provenance(source_type="pubmed", source_id=source_id),
        stance=stance,
        weight=weight,
        recency_year=year,
    )


def test_no_evidence_is_zero_confidence():
    assert aggregate_confidence([]) == 0.0


def test_more_supporting_sources_raise_confidence():
    one = aggregate_confidence([ev("PMID:1")], current_year=YEAR)
    two = aggregate_confidence([ev("PMID:1"), ev("PMID:2")], current_year=YEAR)
    assert two > one


def test_confidence_never_exceeds_one():
    many = [ev(f"PMID:{i}", weight=0.9) for i in range(50)]
    assert aggregate_confidence(many, current_year=YEAR) <= 1.0


def test_contradiction_lowers_confidence_but_does_not_zero_it():
    supported = aggregate_confidence([ev("PMID:1", weight=0.8)], current_year=YEAR)
    challenged = aggregate_confidence(
        [ev("PMID:1", weight=0.8), ev("PMID:2", stance=Stance.CONTRADICTS, weight=0.8)],
        current_year=YEAR,
    )
    assert 0.0 < challenged < supported


def test_older_evidence_counts_for_less():
    fresh = aggregate_confidence([ev("PMID:1", year=YEAR)], current_year=YEAR)
    stale = aggregate_confidence([ev("PMID:1", year=YEAR - 10)], current_year=YEAR)
    assert stale < fresh


def test_recency_decay_has_a_floor():
    ancient = aggregate_confidence([ev("PMID:1", weight=1.0, year=1950)], current_year=YEAR)
    assert ancient >= 0.5


def test_dedup_keeps_strongest_item_per_source_and_stance():
    kept = dedup_evidence([ev("PMID:1", weight=0.2), ev("PMID:1", weight=0.9)])
    assert len(kept) == 1
    assert kept[0].weight == 0.9


def test_dedup_keeps_opposing_stances_from_one_source():
    # A single paper can support one claim and contradict another reading of it.
    kept = dedup_evidence([ev("PMID:1"), ev("PMID:1", stance=Stance.CONTRADICTS)])
    assert len(kept) == 2


def test_rescoring_deduped_evidence_is_stable():
    # Re-ingesting the same source must not inflate confidence.
    once = aggregate_confidence(dedup_evidence([ev("PMID:1")]), current_year=YEAR)
    twice = aggregate_confidence(dedup_evidence([ev("PMID:1"), ev("PMID:1")]), current_year=YEAR)
    assert once == twice
