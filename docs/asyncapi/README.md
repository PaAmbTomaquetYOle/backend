# AsyncAPI — Kafka event contract

`asyncapi.yml` is the machine-readable source of truth for the Kafka events
exchanged between `backend` and `slack-agent` (BE-9 / BE-11). It replaces the
prose table that used to live only in the top-level `README.md`.

## Why it lives here (backend)

The backend is the owner of this contract: it produces all 5 outbound
(`offboarding.*`) events and consumes all 5 inbound (`slack-agent.*`) events.
Keeping the spec next to the code that implements both sides — rather than in
a separate shared repo — means one PR can update the domain event, its
handler, and the contract together, and there's no cross-repo sync step for
the side that actually owns the behavior.

## How it stays in sync with the code

There is no automatic codegen-to-runtime wiring (see [Codegen](#codegen)
below) — this is deliberate for now, to avoid a large refactor mid-hackathon.
Instead:

1. When an event's payload changes (new/removed field, new event type, new
   topic), update `asyncapi.yml` by hand in the **same PR** as the code
   change.
2. Run `npm run validate` before pushing.
3. If the change affects what slack-agent consumes/produces, mention it in
   the PR description — slack-agent should re-run `npm run models:ts` (or
   pull the regenerated files) to pick up the new shape.

The corresponding source files, if you need to double check a payload by
hand:

- Envelope: `src/app/domain/events/base.py`
- Outbound event factories: `src/app/domain/events/offboarding_events.py`,
  `src/app/domain/events/sop_events.py`
- Inbound event types: `src/app/domain/events/inbound_events.py`
- Inbound payload shapes: `src/app/application/services/handlers/*.py`
  (each handler's docstring states "Expected payload: ...")
- Topic naming/prefixes: `src/app/infrastructure/adapters/events/topics.py`,
  `src/app/infrastructure/config/settings.py`

## Usage

```bash
npm install
```

| Command | What it does |
|---|---|
| `npm run validate` | Runs `asyncapi validate` — fails if the spec is malformed. |
| `npm run html` | Generates static HTML docs into `./html` (open `html/index.html`). Also generated automatically if you just want to look at the contract; not committed (see `.gitignore`). |
| `npm run models:py` | Generates Python models into `./generated/python` (package `offboardme_events`). |
| `npm run models:ts` | Generates TypeScript interfaces into `./generated/ts`. |

You can also skip local tooling entirely and paste `asyncapi.yml` into
[AsyncAPI Studio](https://studio.asyncapi.com/) to visualize it.

## Codegen — status and next steps

- **Python**: models are generated for reference under `./generated/python`.
  They are **not** wired into the runtime — the backend's `DomainEvent` is a
  plain dataclass with an untyped `payload: dict`, and switching every
  producer/handler to the generated Pydantic models is a larger refactor
  (typed payload construction + validation on both publish and consume
  paths) intentionally left out of BE-11's scope.
- **TypeScript**: models are generated for reference under `./generated/ts`.
  They are meant to be adopted by `slack-agent` (a separate repo) — see the
  tracking issue for that adoption work, since this PR does not touch the
  `slack-agent` repository.
- Neither `./generated/**` nor `./html` is regenerated automatically in CI
  today; only `asyncapi validate` would run if a validate-in-CI job is added
  (see the main `README.md`/PR description for that call).
