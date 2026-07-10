# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FastAPI backend for **BrainTrust** (OffboardMe) — orchestrates the offboarding lifecycle (interview → dossier → completion), consumes Kafka events published by `slack-agent`, and delegates dossier writing to `mcp-server`'s `generate_dossier` tool. See the parent `../CLAUDE.md` for how this fits with `slack-agent` and `mcp-server`, and `README.md` for the full Kafka topic table and AsyncAPI contract details.

## Commands

```bash
uv sync                                                                       # install deps
DB_PASSWORD=test NEO4J_PASSWORD=test KAFKA_CLUSTER_ID=test JWT_SECRET=test uv run pytest   # run tests (env vars required even for unit tests)
uv run pytest tests/domain/test_offboarding_process.py                       # single test file
uv run pytest tests/domain/test_offboarding_process.py::test_name -v          # single test
uv run pytest --cov-report=html                                              # HTML coverage -> htmlcov/index.html
uv run ruff check .                                                          # lint
```

Local full stack (Postgres, Neo4j, Kafka, Kafka UI) via Docker Compose:

```powershell
.\scripts\start-dev.ps1   # Windows
./scripts/start-dev.sh    # Linux/macOS
```

Requires `.env` (copy from `.env.example`) with real values for `DB_PASSWORD`, `NEO4J_PASSWORD`, `KAFKA_CLUSTER_ID`, `JWT_SECRET`, `SERVICE_CREDENTIALS`. Kafka requires SASL_SSL certs — generate with `./scripts/gen-kafka-certs.sh`.

## Architecture

**Hexagonal**, under `src/app/`:

- **`domain/`** — Entities, value objects, domain events, exceptions. Zero framework dependencies. Lifecycles (`offboarding/`, `interview/`, `dossier/`) are modeled as **State pattern**: each has a `process.py`/entity holding a `state`, plus a `state/` subpackage with one concrete state class per lifecycle stage (e.g. `offboarding/state/{not_started,in_progress,pending_revision,finished,cancelled}.py`), all extending `state/base.py`.
- **`application/`** — `ports/` (interfaces infrastructure must implement — event publisher, dossier generator, graph database, repositories), `service_interfaces/` (contracts services implement), `services/` (use cases: `offboarding_facade_service.py` fronts the others — `offboarding_process_service`, `interview_service`, `dossier_service`, `sop_service`, `knowledge_graph_service`, `token_service`). `services/handlers/` holds one handler per inbound Kafka event type, dispatched by `inbound_event_dispatcher.py`.
- **`infrastructure/`** — `api/routers/` (FastAPI routers — REST is read-only, see below), `adapters/` (`ai/` — `FakeDossierGenerator` / `LLMDossierGenerator`; `events/` — Kafka producer/consumer/DLQ; `graph/` — Neo4j), `persistence/` (SQLModel models + engine), `config/settings.py` (env-driven `Settings`).

### Two composition roots, kept in sync deliberately

`infrastructure/composition.py` is the **single place** that assembles a fully-wired `OffboardingFacadeService` from a `Session` — because it's needed by two different call sites that can't share a DI mechanism:

- **FastAPI routes** build use cases via `Depends` (`infrastructure/api/dependencies.py`), which works because a request has a request-scoped session.
- **The Kafka consumer** (`main.py`) processes messages outside any HTTP request — no `Depends` — so it calls `composition.build_offboarding_facade()` by hand, once per message, with its own session.

When adding a new service or dependency to the offboarding facade, wire it in `composition.py`, not ad hoc in either call site.

### REST is read-only — Kafka is the only write path

Every REST endpoint except `POST /auth/token` and `GET /health*` requires a JWT Bearer token. The API only exposes `GET`/list/search — no `POST/PATCH/DELETE` for offboarding/interview/dossier state. All writes (trigger, cancel, interview turns, dossier generation, SOP creation) arrive as Kafka events on `slack-agent.*` topics and are routed through `InboundEventDispatcher` → the matching handler in `application/services/handlers/`. Malformed messages or handler failures go to the `offboarding.dlq` topic with `source_topic`/`error` headers — the offset is still committed, so a bad message never blocks the consumer.

The canonical contract (topics, envelopes, payload schemas) is `docs/asyncapi/asyncapi.yml` (AsyncAPI 3.0.0) — **if this and the code ever disagree, the spec wins**. Regenerate/validate/visualize from `docs/asyncapi/` (`npm run validate` / `npm run html` / `npm run models:py` / `npm run models:ts`).

### AI dossier generation is pluggable

`IDossierGenerator` decouples dossier content from the rest of the flow. `FakeDossierGenerator` (deterministic, always available) is the fallback; `LLMDossierGenerator` is a thin MCP client that calls mcp-server's `generate_dossier` tool (the LLM itself runs in mcp-server, not here). Feature-flagged via `DOSSIER_LLM_ENABLED` in `main.py`'s lifespan. The whole round trip is wrapped in a timeout + broad `except Exception` — any failure (connection, tool error, malformed JSON) falls back to `FakeDossierGenerator` rather than breaking the Kafka consumer.

### Auth

Client-credentials grant at `POST /api/v1/auth/token` (HS256, `JWT_SECRET`, `aud=JWT_AUDIENCE`). Valid `client_id`/`client_secret` pairs come from `SERVICE_CREDENTIALS` (JSON map, e.g. `slack-agent`/`mcp-server`). Tokens expire after `TOKEN_EXPIRY_SECONDS` (default 300s) — callers cache and refresh, they don't mint their own.
