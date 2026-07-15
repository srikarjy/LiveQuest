"""Runtime configuration, loaded from environment / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Anthropic
    anthropic_api_key: str = ""
    model_reasoning: str = "claude-opus-4-8"  # Hypothesis, Skeptic
    # utility agents: Literature, Drug, Trial, Curator, Evidence, Provenance
    model_utility: str = "claude-haiku-4-5"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "livequest-dev"

    # Investigation budget (soft ceiling; keeps a run to a few dollars)
    max_agent_iterations: int = 6
    evidence_budget: int = 24  # max evidence items gathered before the loop stops

    # Live-data toggle. When False, ingestion runs against committed seed fixtures (deterministic
    # offline demo). When True, it hits the public PubMed E-utilities + Open Targets GraphQL APIs.
    use_live_data: bool = False

    # Public data-source endpoints (free, no auth).
    pubmed_eutils_base: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    open_targets_graphql: str = "https://api.platform.opentargets.org/api/v4/graphql"


settings = Settings()
