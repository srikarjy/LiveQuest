"""Graph domain model: typed nodes/edges carrying evidence + provenance.

The investigation world is a directed graph:

    Disease → Gene → Protein → Drug → AdverseEvent → Trial

Every edge is *earned* — it carries the evidence items that justify it, each with
its own provenance (where the fact came from). Nothing is unattributed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    DISEASE = "Disease"
    GENE = "Gene"
    PROTEIN = "Protein"
    DRUG = "Drug"
    ADVERSE_EVENT = "AdverseEvent"
    TRIAL = "Trial"


class RelType(str, Enum):
    ASSOCIATED_WITH = "ASSOCIATED_WITH"  # Gene↔Disease, Drug↔Disease
    ENCODES = "ENCODES"  # Gene→Protein
    TARGETS = "TARGETS"  # Drug→Gene/Protein
    CAUSES = "CAUSES"  # Drug→AdverseEvent
    TESTED_IN = "TESTED_IN"  # Drug→Trial
    IMPLICATES = "IMPLICATES"  # Trial→Disease


class Stance(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Provenance(BaseModel):
    """Where a single piece of evidence came from."""

    source_type: str  # "pubmed" | "open_targets" | "seed"
    source_id: str  # e.g. "PMID:33188556" or "OT:ENSG00000133019"
    span: str | None = None  # quoted snippet / association detail
    url: str | None = None


class Evidence(BaseModel):
    """One justification for an edge, with a stance and a per-item score."""

    provenance: Provenance
    stance: Stance = Stance.SUPPORTS
    weight: float = 0.5  # 0..1 strength of this single item
    recency_year: int | None = None  # publication year, feeds recency scoring

    @property
    def dedup_key(self) -> str:
        # Same source contributing the same stance counts once — this is what
        # makes edge upserts idempotent.
        return f"{self.provenance.source_id}|{self.stance.value}"


class GraphNode(BaseModel):
    type: NodeType
    name: str
    norm_vocab: str | None = None  # "MedDRA" | "RxNorm" | "EFO" | "Ensembl" ...
    norm_code: str | None = None  # controlled-vocabulary code
    source_id: str | None = None  # raw id if not normalized
    created_at: str = Field(default_factory=_utcnow)

    @property
    def key(self) -> str:
        """Canonical identity used for idempotent MERGE.

        Prefers the normalized vocabulary code; falls back to a raw source id;
        finally to a slugged name so ad-hoc nodes still dedupe.
        """
        if self.norm_vocab and self.norm_code:
            ident = f"{self.norm_vocab}:{self.norm_code}"
        elif self.source_id:
            ident = self.source_id
        else:
            ident = self.name.strip().lower()
        return f"{self.type.value}:{ident}"


class GraphEdge(BaseModel):
    src_key: str
    dst_key: str
    rel: RelType
    evidence: list[Evidence] = Field(default_factory=list)

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.src_key, self.rel.value, self.dst_key)
