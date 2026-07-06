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

All events use the same JSON envelope:

```json
{ "event_id": "<uuid>", "event_type": "<string>", "occurred_at": "<ISO-8601 UTC>", "payload": { ... } }
```

Topics are namespaced by direction so the backend never re-consumes what it just produced.

### Inbound — consumed by backend (published by slack-agent)

Prefix: `slack-agent` (`KAFKA_INBOUND_TOPIC_PREFIX`). Consumer group: `offboardme-backend-consumer` (`KAFKA_CONSUMER_GROUP_ID`).

| Topic | event_type | payload | Effect |
|---|---|---|---|
| `slack-agent.offboarding.triggered` | `offboarding.triggered` | `employee_id, manager_id, employee_name?, manager_name?` | Creates the offboarding process and starts it |
| `slack-agent.interview.completed` | `interview.completed` | `process_id, turns[]` (`turn_type, speaker_role, timestamp, content, order, topic?, sentiment?, answer_text?`) | Saves the collected answers, completes the interview, submits the process for review |
| `slack-agent.dossier.generation_requested` | `dossier.generation_requested` | `process_id` | Generates and persists the dossier (interview is read from the DB), then completes the offboarding process |

### Outbound — produced by backend (consumed by slack-agent)

Prefix: `offboarding` (`KAFKA_TOPIC_PREFIX`).

| Topic | event_type | payload |
|---|---|---|
| `offboarding.offboarding.state_changed` | `offboarding.state_changed` | `process_id, previous_state, new_state, employee_id, manager_id` |
| `offboarding.interview.completed` | `interview.completed` | `interview_id, process_id, completed_at` |
| `offboarding.dossier.generated` | `dossier.generated` | `dossier_id, process_id, interview_id` |
| `offboarding.offboarding.completed` | `offboarding.completed` | `process_id, employee_id, manager_id, dossier_id` |

### Dead-letter queue

Malformed messages or handler failures are published to `offboarding.dlq` (`KAFKA_DLQ_TOPIC`) with `source_topic` and `error` headers, and the offset is committed — a bad message never blocks or crashes the consumer.

> [!NOTE]
> slack-agent does not yet produce these inbound events (it currently talks to the backend over REST). This contract is defined here so both sides can converge on it.

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
