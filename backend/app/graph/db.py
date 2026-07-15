"""Neo4j access layer: provenance-carrying, idempotent graph writes.

Two guarantees this module exists to uphold:

1. **Idempotency** — re-ingesting the same finding never duplicates a node, an
   edge, or an evidence item. Nodes MERGE on ``GraphNode.key``; edges MERGE on
   (src, rel, dst); evidence dedupes on ``Evidence.dedup_key``.
2. **Nothing unattributed** — an edge cannot be written without at least one
   evidence item, and every evidence item carries its provenance.

Evidence is stored on the relationship as a parallel pair of list properties:
``evidence_json`` (the serialized items) and ``evidence_keys`` (their dedup
keys). Neo4j cannot nest objects on a relationship, and it cannot attach a
relationship to a relationship, so reifying evidence into its own node would
cost a join on every read for a set that is small and always read whole.
``confidence`` is denormalized onto the edge so the UI can colour the graph
without recomputing scores per frame.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from importlib import resources
from typing import Any

from neo4j import Driver, GraphDatabase

from app.config import settings
from app.graph.models import Evidence, GraphEdge, GraphNode, NodeType, RelType
from app.scoring import aggregate_confidence, dedup_evidence


class UnattributedEdgeError(ValueError):
    """Raised when an edge write carries no evidence."""


def _serialize(evidence: Iterable[Evidence]) -> tuple[list[str], list[str]]:
    """Split evidence into parallel (json, dedup_key) lists for storage."""
    items = list(evidence)
    return [ev.model_dump_json() for ev in items], [ev.dedup_key for ev in items]


def _deserialize(evidence_json: Iterable[str] | None) -> list[Evidence]:
    if not evidence_json:
        return []
    return [Evidence.model_validate_json(raw) for raw in evidence_json]


class GraphStore:
    """Thin wrapper over the Neo4j driver holding all Cypher in one place."""

    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    @classmethod
    def from_settings(cls) -> GraphStore:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        return cls(driver)

    def close(self) -> None:
        self._driver.close()

    def verify_connectivity(self) -> None:
        self._driver.verify_connectivity()

    @contextmanager
    def _session(self) -> Iterator[Any]:
        with self._driver.session() as session:
            yield session

    # --- schema -------------------------------------------------------------

    def apply_schema(self) -> int:
        """Apply the uniqueness constraints. Safe to run on every startup.

        Returns the number of statements executed.
        """
        raw = resources.files("app.graph").joinpath("schema.cypher").read_text()
        statements = [
            s.strip() for s in raw.split(";") if s.strip() and not s.strip().startswith("//")
        ]
        with self._session() as session:
            for statement in statements:
                session.run(statement)
        return len(statements)

    # --- writes -------------------------------------------------------------

    def upsert_node(self, node: GraphNode) -> str:
        """MERGE a node on its canonical key. Returns the key."""
        with self._session() as session:
            session.execute_write(self._merge_node_tx, node)
        return node.key

    def upsert_nodes(self, nodes: Iterable[GraphNode]) -> list[str]:
        keys = []
        with self._session() as session:
            for node in nodes:
                session.execute_write(self._merge_node_tx, node)
                keys.append(node.key)
        return keys

    @staticmethod
    def _merge_node_tx(tx: Any, node: GraphNode) -> None:
        # Label comes from the NodeType enum, never from free text, so the
        # f-string cannot carry injected Cypher.
        label = NodeType(node.type).value
        tx.run(
            f"""
            MERGE (n:{label} {{key: $key}})
            ON CREATE SET n.created_at = $created_at
            SET n.name = $name,
                n.norm_vocab = $norm_vocab,
                n.norm_code = $norm_code,
                n.source_id = $source_id
            """,
            key=node.key,
            name=node.name,
            norm_vocab=node.norm_vocab,
            norm_code=node.norm_code,
            source_id=node.source_id,
            created_at=node.created_at,
        )

    def upsert_edge(self, edge: GraphEdge) -> float:
        """MERGE an edge, union its evidence with what is already stored, and
        recompute confidence. Returns the new confidence.

        Both endpoints must already exist. Raises ``UnattributedEdgeError`` if
        the edge carries no evidence.
        """
        if not edge.evidence:
            raise UnattributedEdgeError(
                f"edge {edge.src_key} -[{edge.rel.value}]-> {edge.dst_key} has no evidence"
            )
        with self._session() as session:
            return session.execute_write(self._merge_edge_tx, edge)

    @staticmethod
    def _merge_edge_tx(tx: Any, edge: GraphEdge) -> float:
        rel = RelType(edge.rel).value  # enum-validated, safe to interpolate
        existing = tx.run(
            f"""
            MATCH (s {{key: $src}})-[r:{rel}]->(d {{key: $dst}})
            RETURN r.evidence_json AS evidence_json
            """,
            src=edge.src_key,
            dst=edge.dst_key,
        ).single()

        stored = _deserialize(existing["evidence_json"] if existing else None)
        merged = dedup_evidence(stored + edge.evidence)
        confidence = aggregate_confidence(merged)
        evidence_json, evidence_keys = _serialize(merged)

        result = tx.run(
            f"""
            MATCH (s {{key: $src}})
            MATCH (d {{key: $dst}})
            MERGE (s)-[r:{rel}]->(d)
            SET r.evidence_json = $evidence_json,
                r.evidence_keys = $evidence_keys,
                r.evidence_count = $evidence_count,
                r.confidence = $confidence
            RETURN r.confidence AS confidence
            """,
            src=edge.src_key,
            dst=edge.dst_key,
            evidence_json=evidence_json,
            evidence_keys=evidence_keys,
            evidence_count=len(merged),
            confidence=confidence,
        ).single()
        if result is None:
            raise KeyError(f"missing endpoint for {edge.src_key} -[{rel}]-> {edge.dst_key}")
        return float(result["confidence"])

    # --- reads --------------------------------------------------------------

    def get_edge(self, src_key: str, rel: RelType, dst_key: str) -> GraphEdge | None:
        with self._session() as session:
            record = session.run(
                f"""
                MATCH (s {{key: $src}})-[r:{RelType(rel).value}]->(d {{key: $dst}})
                RETURN r.evidence_json AS evidence_json
                """,
                src=src_key,
                dst=dst_key,
            ).single()
        if record is None:
            return None
        return GraphEdge(
            src_key=src_key,
            dst_key=dst_key,
            rel=rel,
            evidence=_deserialize(record["evidence_json"]),
        )

    def counts(self) -> dict[str, int]:
        """Node/edge totals — powers the mission HUD's coverage stats."""
        with self._session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            edges = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        return {"nodes": int(nodes), "edges": int(edges)}

    def unattributed_edges(self) -> int:
        """Edges lacking evidence. The invariant asserts this stays zero."""
        with self._session() as session:
            record = session.run(
                """
                MATCH ()-[r]->()
                WHERE r.evidence_count IS NULL OR r.evidence_count = 0
                RETURN count(r) AS c
                """
            ).single()
        return int(record["c"])

    def clear(self) -> None:
        """Drop all data. Test/demo-reset helper — never called by the app."""
        with self._session() as session:
            session.run("MATCH (n) DETACH DELETE n")
