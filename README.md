# Barberian

Barberian is an API-first universal agent runtime. It is designed to discover approved provider credentials at runtime, route requests by capability and policy, fail over across providers, execute research/media/code workflows, and expose one chat interface.

## Runtime flow

`User Request → Intent → Plan → Capability Discovery → Routing → Execution → Observation → Verification → Retry/Fallback → Finalize`

## Included now

- Environment-based provider discovery with secret values never returned by APIs.
- Approved provider catalog for LLM, search, image, video and audio capabilities.
- Explicit custom-provider slots using `BARBERIAN_PROVIDER_<NAME>_*` environment variables; no artificial provider count limit.
- OpenAI-compatible and Anthropic LLM adapters.
- Tavily and Serper search adapters.
- Replicate, Runway and ElevenLabs media adapters.
- Free-first, fastest, quality-first and balanced routing.
- Circuit breakers, health states, retry/fallback and invalid-output fallback.
- Capability-gap advisor with provider recommendations.
- MCP HTTP JSON-RPC client for tool discovery and calls.
- Versioned Skills boundary and permission/approval controls.
- Parallel multi-query research with source deduplication and quality ordering.
- PostgreSQL metadata schema and idempotent migration runner.
- Google Drive artifact transport with lazy dependencies.
- Controlled subprocess sandbox with timeout/output limits.
- Task queue abstraction and isolated worker runtime.
- Execution event bus and SSE endpoint for live status.
- GitHub REST client using runtime-only credentials.
- Responsive AMOLED-black chat UI with module navigation.

## Run

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:10000`.

## Provider configuration

Copy `.env.example` to `.env` locally, or configure the same variables as runtime secrets in Render. Never commit real API keys.

For an approved provider, set its documented `*_API_KEY`/`*_TOKEN`, endpoint and model variables. For an explicit custom JSON API:

```text
BARBERIAN_PROVIDER_MYAPI_KEY=...
BARBERIAN_PROVIDER_MYAPI_ENDPOINT=https://example.com/api
BARBERIAN_PROVIDER_MYAPI_CAPABILITY=llm
BARBERIAN_PROVIDER_MYAPI_MODEL=example-model
BARBERIAN_PROVIDER_MYAPI_PRICING=free
BARBERIAN_PROVIDER_MYAPI_PRIORITY=50
```

## API

- `GET /api/health`
- `GET /api/status`
- `GET /api/providers`
- `GET /api/providers?check=1` — real minimal provider probes
- `GET /api/models`
- `GET /api/capabilities`
- `GET /api/mcp`
- `GET /api/skills`
- `GET /api/integrations`
- `GET /api/tasks?id=<task-id>`
- `GET /api/events?run_id=<run-id>`
- `POST /api/chat` with `{"message":"..."}`
- `POST /api/tasks` with `{"message":"..."}`

## Database and artifacts

Cloud SQL/PostgreSQL stores metadata, task state, provider metadata, execution events, research metadata and artifact references. Media blobs and API secrets are not stored in PostgreSQL.

Google Drive is the artifact layer. `database/schema.sql` is idempotent and `database/migrate.py` applies it using `DATABASE_URL`.

## Development

```powershell
pytest -q
```

GitHub Actions runs the test suite on every push and pull request.

## Security boundary

Web reads, file creation and image generation are default permissions. Destructive file deletion, Git pushes, MCP installation and external payments require explicit permission/approval. Provider credentials are runtime-only and are not emitted in status, logs or API responses.

## Version

`0.5.0`
