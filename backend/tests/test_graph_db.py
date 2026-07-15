"""Graph-layer tests against a real Neo4j.

Idempotency is the property this step exists to guarantee, and it lives in
MERGE semantics and constraints — a mocked driver would only test the mock. So
these run against a live database and skip when one is not reachable
(`docker compose up neo4j`, or the neo4j service in CI).
"""

from __future__ import annotations

import os

import pytest
from neo4j.exceptions import Neo4jError

from app.graph.db import GraphStore, UnattributedEdgeError
from app.graph.models import Evidence, GraphEdge, GraphNode, NodeType, Provenance, RelType, Stance


@pytest.fixture(scope="module")
def store():
    try:
        s = GraphStore.from_settings()
        s.verify_connectivity()
    except Exception as exc:  # driver raises several unrelated types on no-connection
        # CI sets REQUIRE_NEO4J so a missing database fails loudly instead of
        # skipping these tests into a vacuous green run.
        if os.getenv("REQUIRE_NEO4J"):
            pytest.fail(f"REQUIRE_NEO4J is set but Neo4j is not reachable: {exc}")
        pytest.skip(f"Neo4j not reachable: {exc}")
    s.apply_schema()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def clean(store):
    store.clear()
    yield


def drug(name="semaglutide", code="RxNorm:1991302"):
    vocab, value = code.split(":", 1)
    return GraphNode(type=NodeType.DRUG, name=name, norm_vocab=vocab, norm_code=value)


def adverse_event(name="hepatotoxicity", code="MedDRA:10019663"):
    vocab, value = code.split(":", 1)
    return GraphNode(type=NodeType.ADVERSE_EVENT, name=name, norm_vocab=vocab, norm_code=value)


def evidence(source_id="PMID:33188556", stance=Stance.SUPPORTS, weight=0.6, year=2025):
    return Evidence(
        provenance=Provenance(
            source_type="pubmed", source_id=source_id, span="ALT elevation observed"
        ),
        stance=stance,
        weight=weight,
        recency_year=year,
    )


def causes_edge(src, dst, ev):
    return GraphEdge(src_key=src.key, dst_key=dst.key, rel=RelType.CAUSES, evidence=ev)


# --- schema ---------------------------------------------------------------


def test_apply_schema_is_idempotent(store):
    first = store.apply_schema()
    second = store.apply_schema()  # IF NOT EXISTS — must not raise
    assert first == second > 0


def test_uniqueness_constraint_is_enforced(store):
    store.upsert_node(drug())
    with pytest.raises(Neo4jError):
        # Bypass MERGE to prove the constraint itself is live.
        with store._session() as session:
            session.run("CREATE (n:Drug {key: $key})", key=drug().key)


# --- node upserts ---------------------------------------------------------


def test_reupserting_a_node_does_not_duplicate(store):
    store.upsert_node(drug())
    store.upsert_node(drug())
    assert store.counts()["nodes"] == 1


def test_same_entity_from_two_sources_collapses_to_one_node(store):
    # Different display names, same normalized code — one node.
    store.upsert_node(drug(name="semaglutide"))
    store.upsert_node(drug(name="Ozempic"))
    assert store.counts()["nodes"] == 1


def test_distinct_entities_stay_distinct(store):
    store.upsert_node(drug())
    store.upsert_node(adverse_event())
    assert store.counts()["nodes"] == 2


# --- edge upserts ---------------------------------------------------------


def test_edge_carries_evidence_and_confidence(store):
    d, ae = drug(), adverse_event()
    store.upsert_nodes([d, ae])
    confidence = store.upsert_edge(causes_edge(d, ae, [evidence()]))

    assert confidence > 0
    stored = store.get_edge(d.key, RelType.CAUSES, ae.key)
    assert len(stored.evidence) == 1
    assert stored.evidence[0].provenance.source_id == "PMID:33188556"
    assert stored.evidence[0].provenance.span == "ALT elevation observed"


def test_reingesting_identical_evidence_changes_nothing(store):
    d, ae = drug(), adverse_event()
    store.upsert_nodes([d, ae])
    first = store.upsert_edge(causes_edge(d, ae, [evidence()]))
    second = store.upsert_edge(causes_edge(d, ae, [evidence()]))

    assert first == second  # confidence must not drift upward on re-ingest
    assert store.counts()["edges"] == 1
    assert len(store.get_edge(d.key, RelType.CAUSES, ae.key).evidence) == 1


def test_new_supporting_source_raises_confidence(store):
    d, ae = drug(), adverse_event()
    store.upsert_nodes([d, ae])
    first = store.upsert_edge(causes_edge(d, ae, [evidence("PMID:1")]))
    second = store.upsert_edge(causes_edge(d, ae, [evidence("PMID:2")]))

    assert second > first
    assert store.counts()["edges"] == 1  # unioned onto the same edge
    assert len(store.get_edge(d.key, RelType.CAUSES, ae.key).evidence) == 2


def test_skeptic_contradiction_lowers_stored_confidence(store):
    d, ae = drug(), adverse_event()
    store.upsert_nodes([d, ae])
    supported = store.upsert_edge(causes_edge(d, ae, [evidence("PMID:1", weight=0.8)]))
    challenged = store.upsert_edge(
        causes_edge(d, ae, [evidence("PMID:2", stance=Stance.CONTRADICTS, weight=0.8)])
    )
    assert challenged < supported


def test_edge_without_evidence_is_rejected(store):
    d, ae = drug(), adverse_event()
    store.upsert_nodes([d, ae])
    with pytest.raises(UnattributedEdgeError):
        store.upsert_edge(GraphEdge(src_key=d.key, dst_key=ae.key, rel=RelType.CAUSES, evidence=[]))
    assert store.counts()["edges"] == 0


def test_edge_to_missing_endpoint_is_rejected(store):
    d, ae = drug(), adverse_event()
    store.upsert_node(d)  # ae deliberately not written
    with pytest.raises(KeyError):
        store.upsert_edge(causes_edge(d, ae, [evidence()]))


def test_no_unattributed_edges_after_ingest(store):
    d, ae = drug(), adverse_event()
    store.upsert_nodes([d, ae])
    store.upsert_edge(causes_edge(d, ae, [evidence()]))
    assert store.unattributed_edges() == 0


def test_get_missing_edge_returns_none(store):
    assert store.get_edge("Drug:none", RelType.CAUSES, "AdverseEvent:none") is None
