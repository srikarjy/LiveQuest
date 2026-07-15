# 🧬 LiveQuest — Gamified Biomedical Investigation Platform

Pose a real biomedical question — *"Why is semaglutide showing a liver-toxicity signal?"* — and a team of specialized Claude agents investigates it live: reading the literature, querying drug/target/trial databases, proposing and challenging hypotheses, scoring evidence, and building a **knowledge graph you watch come alive**.

The mission framing (difficulty, evidence found, live confidence %) is a **presentation layer over a serious engineering core**: a Neo4j knowledge graph, a real ingestion pipeline (PubMed + Open Targets), async multi-agent orchestration, provenance on every fact, evidence scoring, and graph algorithms.

> Status: **under active construction** (branch `livequest`). See `~/.claude/plans/prancy-shimmying-zebra.md` for the full plan.

## The agent cast

| Character | Role | Source |
|---|---|---|
| 🧬 Curator | Builds/normalizes the graph (MedDRA/RxNorm) | ingestion |
| 📚 Literature | Finds supporting papers | PubMed |
| 💊 Drug | Drug–target associations | Open Targets |
| 🧪 Trial | Clinical-trial evidence | Open Targets |
| 🧠 Hypothesis | Proposes mechanisms | reasons over graph |
| ⚖️ Skeptic | Finds contradictory evidence | PubMed + graph |
| 🔍 Evidence | Scores confidence | scoring engine |
| 🕵️ Provenance | Tracks origin of every fact | audit store |

## Architecture

- **Graph DB** — Neo4j (`Disease→Gene→Protein→Drug→AdverseEvent→Trial`), every edge carrying evidence + provenance + confidence
- **Backend** — FastAPI (REST + WebSocket streaming of agent + graph events)
- **Frontend** — React + TypeScript + Vite + `react-force-graph` (living graph: pulsing nodes, animated edges, green = high-confidence, red = contradiction)
- **Data** — public PubMed E-utilities + Open Targets GraphQL (free, no auth); deterministic offline seed fixtures for demos

## Quickstart

```bash
cp .env.example .env          # add ANTHROPIC_API_KEY for a live run
docker compose up             # Neo4j + backend + frontend
# frontend → http://localhost:5173   backend → http://localhost:8000/health
```

Local backend dev:

```bash
cd backend && uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload
uv run pytest
```

## Roadmap (stretch)

Multiplayer consensus graphs · XP/level progression unlocking new data sources · "boss battle" hard questions requiring multi-agent collaboration.

---

*The original DeepPromptor Chrome extension lives in [`legacy/`](legacy/).*
