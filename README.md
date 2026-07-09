<div align="center">

![BrainTrust · Backend](https://capsule-render.vercel.app/api?type=waving&color=0:1A2980,100:26D0CE&height=200&section=header&text=BrainTrust%20%C2%B7%20Backend&fontSize=46&fontColor=ffffff&desc=Offboarding%20orchestration%20API%20%E2%80%94%20FastAPI%20%C2%B7%20Kafka%20%C2%B7%20Postgres%20%C2%B7%20Neo4j&descSize=17&descAlignY=62&animation=fadeIn)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![CI](https://github.com/PaAmbTomaquetYOle/backend/actions/workflows/ci.yml/badge.svg)](https://github.com/PaAmbTomaquetYOle/backend/actions/workflows/ci.yml)
[![Architecture: Hexagonal](https://img.shields.io/badge/architecture-hexagonal-6E56CF)](#)

**🔌 [mcp-server](https://github.com/PaAmbTomaquetYOle/mcp-server)** &nbsp;·&nbsp; **🗄️ backend** &nbsp;·&nbsp; **💬 [slack-agent](https://github.com/PaAmbTomaquetYOle/slack-agent)**

</div>

Backend API for the **BrainTrust** offboarding agent — consumes Kafka events published by **slack-agent**, orchestrates the offboarding lifecycle (interview → dossier → completion), and delegates dossier writing to **mcp-server**'s `generate_dossier` tool. Built with FastAPI and hexagonal architecture.

### 📚 Contents

- [🏗 Infrastructure](#-infrastructure)
- [🚀 Getting Started](#-getting-started)
- [🔑 Authentication](#-authentication)
- [📨 Kafka topics](#-kafka-topics)
- [🤖 AI dossier generation](#-ai-dossier-generation)
- [📜 AsyncAPI contract](#-asyncapi-contract)
- [🧪 Testing](#-testing)

## 🏗 Infrastructure

The backend relies on several core services, orchestrated via Docker Compose:

- **PostgreSQL 18**: Relational persistence for standard entities (SQLModel).
- **Neo4j 5**: Graph persistence for complex relationships and dossier context.
- **Apache Kafka (Confluent 7.8.0)**: Event streaming using KRaft mode (no Zookeeper).
- **Kafka UI**: Web interface for inspecting topics and messages.

## 🚀 Getting Started

We provide scripts to spin up the entire local development environment effortlessly.

### Prerequisites
- Docker Desktop or Docker Engine installed and running.
- Python 3.14 (managed via [uv](https://github.com/astral-sh/uv)) if running the backend outside Docker.

### 1. Setup Environment Variables
Copy the example environment file and fill in the required passwords and secrets:
```bash
cp .env.example .env
```
> [!IMPORTANT]
> You **must** provide secure values for `DB_PASSWORD`, `NEO4J_PASSWORD`, `KAFKA_CLUSTER_ID`, `JWT_SECRET`, and `SERVICE_CREDENTIALS` in your `.env` file before starting the stack. The `.env.example` file contains instructions on how to generate the Kafka and JWT secrets. Kafka additionally requires SASL_SSL certs — see [🔐 Kafka transport security](#-kafka-transport-security).

### 2. Start the Development Stack

#### Linux / macOS
```bash
./scripts/start-dev.sh
```

#### Windows (PowerShell)
```powershell
.\scripts\start-dev.ps1
```

The script will build the Docker images and wait until all healthchecks pass. Once completed, the following services will be available:

- 🚀 **FastAPI Backend**: [http://localhost:8888](http://localhost:8888)
- 🌐 **API Documentation**: [http://localhost:8888/docs](http://localhost:8888/docs)
- 📊 **Kafka UI**: [http://localhost:8080](http://localhost:8080)
- 🔵 **Neo4j Browser**: [http://localhost:7474](http://localhost:7474)

> [!TIP]
> The ports above are defaults. You can change them by modifying `API_PORT`, `KAFKA_UI_PORT`, `NEO4J_BROWSER_PORT`, and `DB_PORT` in your `.env` file. The start scripts will automatically adapt to your configured ports.

## 🔑 Authentication

Every REST endpoint except `POST /api/v1/auth/token` and `GET /api/v1/health*` requires a JWT Bearer token (`Authorization: Bearer <token>`), HS256-signed with `JWT_SECRET`, `aud=JWT_AUDIENCE`.

Services obtain a token via the client-credentials grant:

```bash
curl -X POST http://localhost:8888/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"grant_type": "client_credentials", "client_id": "slack-agent", "client_secret": "<secret>"}'
```

Valid `client_id`/`client_secret` pairs are configured via `SERVICE_CREDENTIALS` (a JSON object, e.g. `{"slack-agent": "<secret>", "mcp-server": "<secret>"}`) — see `.env.example`. Tokens expire after `TOKEN_EXPIRY_SECONDS` (default 300s); callers should cache and refresh rather than minting their own tokens.

## 📨 Kafka topics

> [!IMPORTANT]
> This section is a human-readable summary. The **machine-readable source of
> truth** is the [AsyncAPI contract](#-asyncapi-contract) at
> `docs/asyncapi/asyncapi.yml` — if this table and the spec ever disagree,
> the spec (and the code it was derived from) wins.

All events use the same JSON envelope:

```json
{ "event_id": "<uuid>", "event_type": "<string>", "occurred_at": "<ISO-8601 UTC>", "payload": { ... } }
```

Topics are namespaced by direction so the backend never re-consumes what it just produced. The Kafka record key is `payload.process_id` when present, otherwise it falls back to `event_id`.

### Inbound — consumed by backend (published by slack-agent)

Prefix: `slack-agent` (`KAFKA_INBOUND_TOPIC_PREFIX`). Consumer group: `offboardme-backend-consumer` (`KAFKA_CONSUMER_GROUP_ID`).

| Topic | event_type | payload | Effect |
|---|---|---|---|
| `slack-agent.offboarding.triggered` | `offboarding.triggered` | `employee_id, manager_id, employee_name?, manager_name?` | Creates the offboarding process and starts it |
| `slack-agent.interview.started` | `interview.started` | `process_id` | Creates the interview if needed and marks it in progress (idempotent — skipped if already past `SCHEDULED`) |
| `slack-agent.interview.completed` | `interview.completed` | `process_id, turns[]` (`turn_type, speaker_role, timestamp, content, order, topic?, sentiment?, answer_text?`) | Saves the collected answers, completes the interview, submits the process for review |
| `slack-agent.dossier.generation_requested` | `dossier.generation_requested` | `process_id` | Generates and persists the dossier (interview is read from the DB), then completes the offboarding process |
| `slack-agent.sop.creation_requested` | `sop.creation_requested` | `content, author, origin_channel, tags?` | Creates a SOP from a Slack-originated request |

### Outbound — produced by backend (consumed by slack-agent)

Prefix: `offboarding` (`KAFKA_TOPIC_PREFIX`).

| Topic | event_type | payload |
|---|---|---|
| `offboarding.offboarding.state_changed` | `offboarding.state_changed` | `process_id, previous_state, new_state, employee_id, manager_id` |
| `offboarding.interview.completed` | `interview.completed` | `interview_id, process_id, completed_at` |
| `offboarding.dossier.generated` | `dossier.generated` | `dossier_id, process_id, interview_id` |
| `offboarding.offboarding.completed` | `offboarding.completed` | `process_id, employee_id, manager_id, dossier_id` |
| `offboarding.sop.created` | `sop.created` | `sop_id, author, origin_channel, tags[], version, created_at` |

> [!NOTE]
> `interview.completed` exists on **both** sides with different payloads: the inbound version carries the raw `turns[]` collected during the interview, while the outbound version is a lightweight notification (`interview_id, process_id, completed_at`) that the backend finished persisting it.

### Dead-letter queue

Malformed messages or handler failures are published to `offboarding.dlq` (`KAFKA_DLQ_TOPIC`) with `source_topic` and `error` headers, and the offset is committed — a bad message never blocks or crashes the consumer.

> [!NOTE]
> slack-agent does not yet produce these inbound events (it currently talks to the backend over REST). This contract is defined here so both sides can converge on it.

### 🔐 Kafka transport security

The broker requires **SASL_SSL** (SCRAM-SHA-512 over TLS) — plaintext connections are rejected. Generate local certs and a SCRAM user with:

```bash
./scripts/gen-kafka-certs.sh
```

This writes broker keystore/truststore material and a client CA (`certs/ca.pem`) that `slack-agent` and the backend both need to connect. Set `KAFKA_SECURITY_PROTOCOL=SASL_SSL`, `KAFKA_SASL_USERNAME`, `KAFKA_SASL_PASSWORD`, and `KAFKA_SSL_CAFILE` in `.env` (see `.env.example`). Certificate provisioning and secret storage for non-local environments is a devops decision, out of scope here.

## 🤖 AI dossier generation

`IDossierGenerator` (`src/app/application/ports/dossier_generator.py`) decouples dossier content generation from the rest of the offboarding flow. Two implementations exist:

- **`FakeDossierGenerator`** — deterministic placeholder, copies interview answers into a single `ResponsibilitiesSection`. Always available, used as the fallback.
- **`LLMDossierGenerator`** (`src/app/infrastructure/adapters/ai/llm_dossier_generator.py`) — a thin **MCP client**. The model itself does not live in the backend: this adapter formats the interview transcript and calls mcp-server's `generate_dossier` tool, which runs the LLM (with its own context tools — prior dossiers, SOP search) and returns typed dossier content. Keeping the model in mcp-server means the backend never needs an LLM SDK or API key, and the same generation capability is reusable by any other MCP client.

  **Prompt/contract**: the interview's turns (`InterviewQuestion.answer_text`, `InterviewNote.content`) are flattened into a plain Q/A transcript, sent as the `interview_transcript` argument to `generate_dossier`. The tool's result is a JSON object shaped like `{"summary": ..., "sections": [...]}`, one entry per section type (`responsibilities`, `contacts`, `pending_tasks`, `knowledge_areas`) using the `section_type` discriminator — see mcp-server's `DossierGenerationService` for the actual prompt and tool-use loop. `dossier_response_parser.py` validates and maps that JSON into typed domain objects on this side — any shape mismatch raises and triggers the fallback.

  **Error handling**: the whole mcp-server round trip (connection, tool call, and the generation it runs) is wrapped in a timeout (`DOSSIER_LLM_TIMEOUT_SECONDS`) and a broad `except Exception`. A connection failure, a tool error, or a malformed JSON answer all fall back to `FakeDossierGenerator` — the Kafka consumer's flow never breaks.

Wiring (`src/app/main.py`, lifespan) is feature-flagged: set `DOSSIER_LLM_ENABLED=true` to use `LLMDossierGenerator` (pointed at `MCP_SERVER_URL`); otherwise it stays on `FakeDossierGenerator`. See `.env.example` for `DOSSIER_LLM_*` / `MCP_SERVER_URL`. Running mcp-server locally (`uv run mcp-server` in that repo, with its own `MCP_SERVER_ANTHROPIC_API_KEY` set) exposes the streamable-HTTP endpoint at `MCP_SERVER_URL` (default `/mcp` path).

## 📜 AsyncAPI contract

The full, machine-readable event contract — all 10 topics above plus the DLQ, with envelopes, payload schemas and pub/sub direction — lives at [`docs/asyncapi/asyncapi.yml`](docs/asyncapi/asyncapi.yml) (AsyncAPI 3.0.0).

```bash
cd docs/asyncapi
npm install
```

- **Visualize**: paste `asyncapi.yml` into [AsyncAPI Studio](https://studio.asyncapi.com/), or generate static HTML locally:
  ```bash
  npm run html   # writes ./html/index.html
  ```
- **Validate** (fails CI-style if the spec is malformed):
  ```bash
  npm run validate
  ```
- **Generate types** from the spec, for reference/adoption on either side of the contract:
  ```bash
  npm run models:py   # Pydantic-friendly Python models -> ./generated/python
  npm run models:ts   # TypeScript interfaces        -> ./generated/ts
  ```

See [`docs/asyncapi/README.md`](docs/asyncapi/README.md) for why the spec lives in this repo and how to keep it in sync with the code.

## 🧪 Testing

The backend includes a comprehensive test suite. To run tests locally using `uv`:

```bash
# Ensure required variables are present (can be dummy values for tests)
DB_PASSWORD=test NEO4J_PASSWORD=test KAFKA_CLUSTER_ID=test JWT_SECRET=test uv run pytest
```

Coverage is measured automatically (`pytest-cov`) and printed as a terminal table. For an HTML report:

```bash
DB_PASSWORD=test NEO4J_PASSWORD=test KAFKA_CLUSTER_ID=test JWT_SECRET=test uv run pytest --cov-report=html
# then open htmlcov/index.html
```

---

<div align="center">

Part of **BrainTrust** — fighting knowledge loss from volunteer turnover in NGOs.

[mcp-server](https://github.com/PaAmbTomaquetYOle/mcp-server) &nbsp;·&nbsp; [slack-agent](https://github.com/PaAmbTomaquetYOle/slack-agent) &nbsp;·&nbsp; MIT © [Pa Amb Tomàquet Y Olé](LICENSE)

</div>
