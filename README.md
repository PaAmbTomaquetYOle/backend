# OffBoardMe Backend

Backend API for the OffBoardMe Slack Agent, built with FastAPI and hexagonal architecture.

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
> You **must** provide secure values for `DB_PASSWORD`, `NEO4J_PASSWORD`, `KAFKA_CLUSTER_ID`, and `JWT_SECRET` in your `.env` file before starting the stack. The `.env.example` file contains instructions on how to generate the Kafka and JWT secrets.

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

## 🤖 AI dossier generation

`IDossierGenerator` (`src/app/application/ports/dossier_generator.py`) decouples dossier content generation from the rest of the offboarding flow. Two implementations exist:

- **`FakeDossierGenerator`** — deterministic placeholder, copies interview answers into a single `ResponsibilitiesSection`. Always available, used as the fallback.
- **`LLMDossierGenerator`** (`src/app/infrastructure/adapters/ai/llm_dossier_generator.py`) — the real adapter. Rather than issuing a single isolated completion, it acts as an **MCP client of `mcp-server`** (the same tool surface `slack-agent` drives during the interview), so the model can pull extra context before writing the dossier:
  - `get_dossier` — look up prior dossiers (e.g. earlier processes for the same employee, or how similar roles were documented).
  - `test_search_query` — search the org's cached SOP index for knowledge related to topics raised in the interview.

  Only these two read-only, tokenless tools are exposed; the Jira/Trello/Slack tools on mcp-server require a per-user OAuth session that has no meaning for a headless Kafka consumer.

  **Prompt strategy**: the interview's turns (`InterviewQuestion.answer_text`, `InterviewNote.content`) are flattened into a plain Q/A transcript and sent as the user message; a system prompt instructs the model on when to use the tools and to end the conversation with a single JSON object shaped like `{"summary": ..., "sections": [...]}`, one entry per `DossierSection` subtype (`responsibilities`, `contacts`, `pending_tasks`, `knowledge_areas`). `dossier_response_parser.py` validates and maps that JSON into the typed domain objects — any shape mismatch raises and triggers the fallback.

  **Error handling**: the whole call (mcp-server connection, tool round trips, completions) is wrapped in a timeout (`DOSSIER_LLM_TIMEOUT_SECONDS`) and a broad `except Exception`. A connection failure, a malformed JSON answer, or an exhausted tool-call budget (`DOSSIER_LLM_MAX_TOOL_ITERATIONS`) all fall back to `FakeDossierGenerator` — the Kafka consumer's flow never breaks.

Wiring (`src/app/main.py`, lifespan) is feature-flagged: set `DOSSIER_LLM_ENABLED=true` and `ANTHROPIC_API_KEY` to use `LLMDossierGenerator`; otherwise (or if the key is missing) it falls back to `FakeDossierGenerator` at startup. See `.env.example` for the full list of `DOSSIER_LLM_*` / `ANTHROPIC_*` / `MCP_SERVER_URL` variables. Running mcp-server locally (`uv run mcp-server` in that repo) exposes its streamable-HTTP endpoint at `MCP_SERVER_URL` (default `/mcp` path).

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
