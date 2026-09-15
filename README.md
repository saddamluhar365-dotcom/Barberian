# Barberian

API-first universal AI agent runtime. The repository is designed around capability discovery, provider routing, failover, task orchestration, MCP, Skills, research, media, sandbox, GitHub workflows, artifact storage, security and observability.

## Architecture

`User Request → Understand → Context → Plan → Task Graph → Capability Discovery → Routing → Execution → Observation → Verification → Retry/Fallback → Finalize`

### Runtime responsibilities

- Provider discovery from environment variable names without exposing secret values.
- Approved provider catalog and adapter boundary.
- Free-first, fastest, quality-first and balanced routing.
- Health-aware provider ranking and circuit breakers.
- Primary → standby → fallback execution with request context preserved.
- Dependency-aware parallel task execution with cycle detection.
- Checkpoints and deterministic idempotency keys for resumable work.
- MCP server/tool registry and versioned Skills registry.
- Research, media, sandbox and GitHub workflow boundaries.
- Private memory boundary; only verified shared-safe memory can be exported.
- PostgreSQL metadata schema; media/secrets are not stored in SQL blobs.
- Render deployment blueprint with separate web and worker processes.
- Chat UI with module navigation and health status.

## Run locally

```powershell
python app.py
```

Open `http://localhost:10000`.

## Environment

Copy `.env.example` to `.env` for local configuration. In production, put secrets in the runtime secret store (for example Render environment secrets). Never commit API keys.

## API

- `GET /api/health` — liveness
- `GET /api/status` — runtime status and provider snapshot
- `GET /api/providers` — refresh and list discovered provider credentials (never secret values)
- `POST /api/chat` — primary chat entry point

## Database

`database/schema.sql` contains the PostgreSQL metadata model for users, workspaces, projects, conversations, tasks, execution runs/events, providers, MCP, Skills, artifacts, research, video jobs, memory, logs, errors, audit events and permissions.

## Deployment

`render.yaml` defines the web API and isolated worker services. Cloud SQL is the persistent metadata database and Google Drive/object storage is the artifact layer; credentials are runtime-only.

## Development

```powershell
pytest -q
```

GitHub Actions runs the test suite on pushes and pull requests.

## Status

The architecture is implemented incrementally. External provider adapters, cloud database repositories, Drive transport, MCP transports, production sandbox backends and media renderers are explicit extension points; they are not falsely represented as complete merely because their interfaces exist.
