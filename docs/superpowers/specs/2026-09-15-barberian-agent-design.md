# Barberian Agent Design

## Goal
Build a minimal API-first agent controlled from one chat interface, with chat-driven MCP and Skill registration.

## Principles
- Keep only necessary files and code.
- No fixed/local LLM dependency.
- Provider/API capabilities are discovered and routed at runtime.
- MCP and Skills are first-class capabilities but share one lightweight manager.
- Secrets stay in runtime environment variables, never in the database or chat.
- Unknown integrations are validated before registration or execution.
- Long-running work must be resumable as the system grows.

## Core Flow
`Chat -> Agent -> Plan -> Capability Router -> Tool/API -> Verify -> Response`

## Chat-controlled MCP and Skills
User commands such as `add GitHub MCP`, `add research skill`, `list MCP`, and `disable skill X` are parsed by the agent. The manager validates a known integration definition, registers it, runs a basic health check where applicable, and makes it available to the router.

## Initial Implementation Scope
Start with a small Python API service and a single-page web chat. Store MCP/Skill metadata in a lightweight in-process registry initially; the persistence boundary is isolated so Cloud SQL can replace it without changing the chat contract. Provider APIs, Cloud SQL, Google Drive, media, research, sandbox, and durable workers are added in later independently testable phases.

## Safety
Sensitive actions require explicit approval. Arbitrary unknown MCP endpoints are not executed merely because a user mentions them. API keys are read from environment variables only.
