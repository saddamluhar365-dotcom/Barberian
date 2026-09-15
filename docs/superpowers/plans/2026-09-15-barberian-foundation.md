# Barberian Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the smallest working Barberian agent foundation with a chat API, chat-controlled MCP/Skill registration, and a minimal web interface.

**Architecture:** A small Python HTTP API owns agent intent handling and one registry for MCP/Skills. The web client is a single chat page that calls the API. Persistence and external providers remain clean extension points for later phases.

**Tech Stack:** Python 3.12+, standard library HTTP server, vanilla HTML/CSS/JS, pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-barberian-agent-design.md`

## Global Constraints
- Keep only necessary files and code.
- No fixed/local LLM dependency.
- MCP and Skills use one lightweight manager.
- Secrets are read from environment variables only.
- Unknown integrations are not executed blindly.
- Every behavior change gets a test first.

---

## Task 1: Core registry and intent parsing

Files:
- `barberian/agent.py` — minimal command parsing and response generation.
- `barberian/registry.py` — MCP/Skill registration and status.
- `tests/test_agent.py` — failing tests for supported chat commands.

Steps:
- [ ] Write tests for add/list/disable MCP and Skill commands.
- [ ] Run tests and confirm they fail for the expected missing behavior.
- [ ] Implement the smallest registry and parser that satisfy the tests.
- [ ] Run the tests again.

## Task 2: API and chat page

Files:
- `app.py` — HTTP API and static web serving.
- `web/index.html` — minimal chat UI.
- `tests/test_app.py` — API behavior tests.

Steps:
- [ ] Write tests for chat request/response and static page availability.
- [ ] Verify the new tests fail.
- [ ] Implement the minimal HTTP endpoints.
- [ ] Run all tests.

## Task 3: Configuration and documentation

Files:
- `.env.example` — non-secret configuration names only.
- `requirements.txt` — only required runtime/test dependency.
- `README.md` — run instructions and supported chat commands.

Steps:
- [ ] Add only required configuration/dependency entries.
- [ ] Document local run and command examples.
- [ ] Run the complete test suite and a basic server smoke test.

## Verification
- [ ] All tests pass.
- [ ] The chat page loads.
- [ ] MCP/Skill commands register and change status.
- [ ] No secret values are stored in source files.
- [ ] Repository contains no unnecessary generated artifacts.
