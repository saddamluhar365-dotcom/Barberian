# Barberian UI Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the CSP-incompatible monolithic Barberian frontend with a production-quality same-origin Vanilla HTML/CSS/JavaScript interface that preserves the existing API contract and renders reliably on desktop and mobile.

**Architecture:** `web/index.html` will contain semantic DOM only and load same-origin external assets. `web/css/app.css` owns the complete responsive AMOLED visual system; modular JavaScript files own API access, state, chat lifecycle, history, Markdown safety, and UI behavior. `app.py` will serve only safe static frontend assets with correct MIME types while preserving the strict CSP and existing API routes.

**Tech Stack:** Python 3.12, stdlib `http.server`, Vanilla HTML5/CSS3/ES modules, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-15-barberian-ui-rebuild-design.md`

## Global Constraints

- Preserve the strict CSP; never add `unsafe-inline` merely to make the UI work.
- All executable frontend code and styling must be same-origin external files.
- Preserve the existing Barberian API endpoints and request payload contracts.
- Keep user/agent content escaped before HTML rendering.
- External Markdown links must be restricted to HTTP(S) and use `noopener noreferrer`.
- Do not expose provider secrets, environment variables, or stack traces in the UI.
- Static assets must use correct MIME types and predictable cache policy.
- Pure black AMOLED page background; no gradients or browser-default giant controls.
- Desktop uses a fixed left navigation; mobile uses a drawer and overlay.
- Composer remains bottom anchored and accounts for safe-area insets.
- Every visible interactive control has a deterministic action or is explicitly status-only.
- Do not introduce React/Vue/CDN dependencies.
- Do not claim file upload support because no backend upload API exists.
- Do not claim true live streaming; `/api/events` remains a post-run event replay fetch unless the frontend explicitly consumes it incrementally.

---

## File Map

### Frontend
- Create: `web/css/app.css` — all visual tokens, layout, responsive rules, focus states, safe-area handling, and component styles.
- Create: `web/js/api.js` — same-origin fetch wrappers for health/status/providers/models/capabilities/MCP/skills/integrations/tasks/events/chat.
- Create: `web/js/state.js` — chat/settings state, IDs, localStorage persistence, and state transitions.
- Create: `web/js/markdown.js` — HTML escaping and safe Markdown rendering.
- Create: `web/js/history.js` — conversation listing, search filtering, active chat selection, and history clearing.
- Create: `web/js/chat.js` — welcome/message rendering, send/stop lifecycle, loading/error states, and API result handling.
- Create: `web/js/ui.js` — DOM bindings, sidebar/mobile drawer, settings panel, composer behavior, toasts, and action routing.
- Create: `web/js/app.js` — bootstrap, module wiring, health polling, and application initialization.
- Modify: `web/index.html` — semantic shell with external CSS and module script references; no inline `<style>` or executable inline `<script>`.

### Backend
- Modify: `app.py` — serve `/`, `/index.html`, `/css/*.css`, and `/js/*.js` safely with correct MIME types and cache policy without changing API semantics or weakening CSP.

### Tests
- Modify: `tests/test_web_ui.py` — assert external asset references and required UI contract.
- Modify: `tests/test_web_ui_black_shell.py` — assert visual/responsive/action contract against external CSS and semantic HTML.
- Create: `tests/test_static_assets.py` — exercise the HTTP handler for HTML/CSS/JS content types, safe paths, and security headers.
- Modify: `tests/test_app.py` — retain health regression coverage and add a static asset smoke check if needed.

---

### Task 1: Lock the CSP-Compatible Frontend Contract With Failing Tests

**Files:**
- Modify: `tests/test_web_ui.py`
- Modify: `tests/test_web_ui_black_shell.py`
- Create: `tests/test_static_assets.py`

**Interfaces:**
- Consumes: current `web/index.html`, `app.Handler`, and existing API behavior.
- Produces: deterministic regression tests that fail until external assets and static routing are implemented.

- [ ] **Step 1: Write failing HTML asset tests**

Add tests equivalent to:

```python

def test_index_uses_external_assets_without_inline_execution():
    assert '<link rel="stylesheet" href="/css/app.css">' in HTML
    assert '<script type="module" src="/js/app.js"></script>' in HTML
    assert '<style' not in HTML.lower()
    assert '<script>' not in HTML.lower()
```

- [ ] **Step 2: Write failing static asset tests**

Add a server smoke test that starts `run(host="127.0.0.1", port=10002)` and requests `/`, `/css/app.css`, and `/js/app.js`, asserting 200 responses, HTML/CSS/JavaScript content types, and the strict CSP header.

- [ ] **Step 3: Strengthen the responsive contract tests**

Assert that the external stylesheet contains `@media (max-width: 760px)`, `100dvh`, `env(safe-area-inset-bottom)`, and that the HTML still contains required IDs/actions such as `app`, `sidebar`, `messages`, `composer`, `mobileMenu`, `themeToggle`, `new-chat`, `search`, `settings`, `attach`, `send`, `stop`, and `clear-chat`.

- [ ] **Step 4: Run the targeted tests and verify failure**

Run:

```powershell
pytest tests/test_web_ui.py tests/test_web_ui_black_shell.py tests/test_static_assets.py -q
```

Expected: FAIL because the current frontend still embeds CSS/JavaScript and `app.py` does not serve the external asset paths.

- [ ] **Step 5: Commit the failing-test checkpoint**

```powershell
git add tests/test_web_ui.py tests/test_web_ui_black_shell.py tests/test_static_assets.py
git commit -m "test: lock CSP-compatible frontend contract"
```

---

### Task 2: Implement Safe Static Asset Serving

**Files:**
- Modify: `app.py`
- Test: `tests/test_static_assets.py`

**Interfaces:**
- Consumes: `WEB` and `_security_headers` from `app.py`.
- Produces: `serve_static(path)` behavior through `Handler.do_GET`, serving only files under `web/` with explicit MIME types.

- [ ] **Step 1: Add explicit static-root and MIME mapping**

Use a `WEB_ROOT = Path(__file__).parent / "web"` constant and a mapping for `.html`, `.css`, and `.js`. Do not use unrestricted filesystem paths from the URL.

- [ ] **Step 2: Add safe static path resolution**

Implement a helper that strips the leading slash, resolves the requested path relative to `WEB_ROOT`, and rejects traversal or non-file paths. Requests outside the web root must return the existing JSON 404 response rather than exposing filesystem content.

- [ ] **Step 3: Serve HTML and assets with correct headers**

Keep HTML `Cache-Control: no-store, max-age=0, must-revalidate` and use deterministic static-asset caching such as `Cache-Control: public, max-age=3600` for CSS/JS. Send `text/html; charset=utf-8`, `text/css; charset=utf-8`, and `application/javascript; charset=utf-8` respectively. Apply `_security_headers()` to every static response.

- [ ] **Step 4: Route static paths before the JSON 404 fallback**

Handle `/`, `/index.html`, `/css/...`, and `/js/...` through the static helper while leaving all `/api/...` routes unchanged.

- [ ] **Step 5: Run static and API tests**

Run:

```powershell
pytest tests/test_static_assets.py tests/test_app.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit backend static serving**

```powershell
git add app.py tests/test_static_assets.py
git commit -m "feat: serve CSP-compatible frontend assets"
```

---

### Task 3: Replace the Monolithic HTML With the Semantic Shell

**Files:**
- Modify: `web/index.html`
- Test: `tests/test_web_ui.py`

**Interfaces:**
- Consumes: existing DOM IDs/actions and API contracts.
- Produces: stable DOM hooks consumed by `ui.js`, `chat.js`, `history.js`, and `app.js`.

- [ ] **Step 1: Write the complete semantic HTML shell**

Keep the existing major IDs and deterministic action attributes, including sidebar navigation, topbar controls, messages, settings panel, composer, attachment area, overlay, and toast. Use accessible button labels and `type="button"` except for the composer submit control.

- [ ] **Step 2: Add external asset references**

Use exactly:

```html
<link rel="stylesheet" href="/css/app.css">
<script type="module" src="/js/app.js"></script>
```

Do not add inline event handlers, `<style>`, or executable inline scripts.

- [ ] **Step 3: Keep visible controls truthful**

The attachment control may select a local file for display only; it must not imply server upload. The theme control must remain a local UI preference or be presented as status-only if no alternate theme exists. Do not create decorative controls with no defined behavior.

- [ ] **Step 4: Run HTML contract tests**

```powershell
pytest tests/test_web_ui.py tests/test_web_ui_black_shell.py -q
```

Expected: PASS after the external CSS/JS tests are satisfied by the shell references and required DOM hooks.

- [ ] **Step 5: Commit the semantic shell**

```powershell
git add web/index.html tests/test_web_ui.py tests/test_web_ui_black_shell.py
git commit -m "refactor: split Barberian semantic frontend shell"
```

---

### Task 4: Build the AMOLED Responsive CSS System

**Files:**
- Create: `web/css/app.css`
- Test: `tests/test_web_ui_black_shell.py`

**Interfaces:**
- Consumes: semantic classes and IDs from `web/index.html`.
- Produces: layout/styling contract for the JavaScript-rendered UI.

- [ ] **Step 1: Define visual tokens and reset**

Use a pure black page background, white primary text, muted secondary text, subtle borders, compact radii, system font stack, `box-sizing: border-box`, and no gradients. Prevent document-level scrolling while allowing the chat/history/panel containers to scroll.

- [ ] **Step 2: Implement desktop shell**

Use a fixed-width sidebar around 280px, full-height main surface, compact topbar, constrained message column, and a bottom-anchored composer. Ensure flex/grid children use `min-height: 0` so the chat region is the scroll container rather than the entire page.

- [ ] **Step 3: Implement welcome and message layouts**

Center the welcome state in usable chat space, provide four responsive quick-action cards, use consistent message spacing/max-width, and style code blocks/action rows without giant cards or browser defaults.

- [ ] **Step 4: Implement mobile drawer and safe area**

At `max-width: 760px`, convert the sidebar into a drawer, show the overlay while open, hide desktop-only controls, keep chat full width, use `100dvh`, and pad the composer with `max(..., env(safe-area-inset-bottom))`.

- [ ] **Step 5: Add accessibility states and reduced-motion support**

Provide `:focus-visible`, hover, disabled, and reduced-motion behavior. Ensure buttons remain usable without relying on color alone.

- [ ] **Step 6: Run stylesheet contract tests**

```powershell
pytest tests/test_web_ui_black_shell.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit CSS**

```powershell
git add web/css/app.css tests/test_web_ui_black_shell.py
git commit -m "feat: add responsive AMOLED Barberian stylesheet"
```

---

### Task 5: Add API and State Modules

**Files:**
- Create: `web/js/api.js`
- Create: `web/js/state.js`

**Interfaces:**
- Consumes: existing `/api/*` routes.
- Produces: `apiGet(path)`, `apiPost(path, payload, options)`, and state functions for chats/settings/persistence.

- [ ] **Step 1: Implement fetch primitives**

`apiGet(path, options = {})` and `apiPost(path, payload, options = {})` must use same-origin relative URLs, check `response.ok`, parse JSON, and throw a sanitized error object/message without exposing response internals.

- [ ] **Step 2: Implement endpoint wrappers**

Expose wrappers for health, status, providers, models, capabilities, MCP, skills, integrations, tasks, events, and chat. `chat(message, signal)` must POST `{message}` to `/api/chat` and support `AbortSignal`.

- [ ] **Step 3: Implement state schema**

Store chats as `{id, title, messages, createdAt, updatedAt}` and settings as `{focusMode, enterSend, localHistory, blackMode}`. Generate IDs client-side and cap persisted history to a reasonable bounded count to avoid unbounded localStorage growth.

- [ ] **Step 4: Implement persistence boundaries**

Use versioned localStorage keys. Catch storage quota/availability errors and continue with in-memory state rather than breaking the UI.

- [ ] **Step 5: Run JavaScript syntax smoke checks**

Use a JavaScript runtime available in CI if present; otherwise run deterministic source assertions from pytest and execute the full test suite later. Do not introduce a frontend dependency solely for syntax checking.

- [ ] **Step 6: Commit API/state modules**

```powershell
git add web/js/api.js web/js/state.js
 git commit -m "feat: add Barberian frontend API and state modules"
```

---

### Task 6: Implement Safe Markdown and Chat Lifecycle

**Files:**
- Create: `web/js/markdown.js`
- Create: `web/js/chat.js`
- Test: `tests/test_web_ui.py`

**Interfaces:**
- Consumes: API `chat()` and state store.
- Produces: `renderMarkdown(source)`, chat rendering functions, and send/stop lifecycle used by `app.js`/`ui.js`.

- [ ] **Step 1: Implement escaping first**

Escape `&`, `<`, `>`, `"`, and `'` before any Markdown transformations. Never interpolate raw message text into `innerHTML`.

- [ ] **Step 2: Implement bounded Markdown support**

Support headings, bold/strong, emphasis, inline code, fenced code blocks, unordered/ordered lists, blockquotes, paragraphs, and HTTP(S) links. For links, validate the URL protocol and add `target="_blank" rel="noopener noreferrer"`.

- [ ] **Step 3: Implement message rendering**

Render user messages as escaped text and agent messages through `renderMarkdown`. Add copy actions only to code blocks/messages where the DOM action is deterministic.

- [ ] **Step 4: Implement send lifecycle**

Disable duplicate sends, add a pending/typing state, create a run ID from the API response, append successful replies, handle empty results, show sanitized API/network errors, and always restore controls in `finally`.

- [ ] **Step 5: Implement cancellation**

Use an `AbortController` for the active request. The stop action must cancel the request and clear the pending state without presenting cancellation as an API failure.

- [ ] **Step 6: Implement post-run event replay**

After a successful chat response containing `run_id`, fetch `/api/events?run_id=...` once and expose the returned events for status/debug presentation without claiming incremental streaming.

- [ ] **Step 7: Run tests**

```powershell
pytest tests/test_web_ui.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit chat/Markdown**

```powershell
git add web/js/markdown.js web/js/chat.js tests/test_web_ui.py
git commit -m "feat: add safe Markdown and chat lifecycle"
```

---

### Task 7: Implement History, Search, Settings, and Mobile UI

**Files:**
- Create: `web/js/history.js`
- Create: `web/js/ui.js`
- Test: `tests/test_web_ui.py`

**Interfaces:**
- Consumes: state functions, chat rendering, semantic DOM hooks.
- Produces: deterministic action routing for every visible interactive control.

- [ ] **Step 1: Implement history rendering/search**

Render persisted chats into the sidebar, mark the active chat, filter titles/content by the search query, and show an explicit empty state. Selecting a history item loads that chat into the message view.

- [ ] **Step 2: Implement new/clear chat**

New chat creates a fresh local conversation and restores the welcome state. Clear history removes local conversations only after a user confirmation path and never calls a server deletion endpoint that does not exist.

- [ ] **Step 3: Implement mobile drawer behavior**

Open/close the sidebar with `mobileMenu`, close on overlay click, close after selecting a history item, and update accessible state attributes such as `aria-expanded`.

- [ ] **Step 4: Implement settings panel**

Wire black mode, focus mode, enter-to-send, local-history, close, and clear-history controls to local state. Keep the panel usable on mobile and never expose runtime/provider secrets.

- [ ] **Step 5: Implement composer controls**

Auto-grow textarea within a bounded height, submit on Enter only when enabled, use Shift+Enter for newline, wire attach/remove display-only behavior, send, and stop controls, and keep focus states accessible.

- [ ] **Step 6: Implement toast/error presentation**

Use a bounded toast component for transient feedback and an inline chat error state for request failures. Do not display raw exception objects or stack traces.

- [ ] **Step 7: Run UI contract tests**

```powershell
pytest tests/test_web_ui.py tests/test_web_ui_black_shell.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit UI modules**

```powershell
git add web/js/history.js web/js/ui.js tests/test_web_ui.py
 git commit -m "feat: add Barberian history and UI controls"
```

---

### Task 8: Wire Application Bootstrap and Full Regression Suite

**Files:**
- Create: `web/js/app.js`
- Modify: `tests/test_app.py` if needed
- Test: all `tests/*.py`

**Interfaces:**
- Consumes: `api.js`, `state.js`, `chat.js`, `history.js`, `ui.js`.
- Produces: a single module entrypoint loaded by `index.html`.

- [ ] **Step 1: Implement bootstrap**

Initialize state, render the current chat/history, bind UI actions, perform the initial health check, and start a low-frequency health refresh that stops cleanly if the page is unloaded.

- [ ] **Step 2: Preserve the existing API contract**

Do not modify endpoint names, payload shape, or backend provider behavior. Frontend failures must remain contained in UI state.

- [ ] **Step 3: Run the complete local suite**

```powershell
pytest -q
```

Expected: PASS with zero failures.

- [ ] **Step 4: Run a source-level CSP audit**

Verify:

```powershell
python -c "from pathlib import Path; s=Path('web/index.html').read_text(encoding='utf-8').lower(); assert '<style' not in s and '<script>' not in s"
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit bootstrap and final local regression**

```powershell
git add web/js/app.js tests/test_app.py
 git commit -m "feat: bootstrap modular Barberian frontend"
```

---

### Task 9: CI Verification and Repair Loop

**Files:**
- Modify only files required by an observed failure.

**Interfaces:**
- Consumes: complete feature branch.
- Produces: a branch whose GitHub Actions test workflow is green.

- [ ] **Step 1: Push the feature branch**

```powershell
git push -u origin feat/ui-accurate-rebuild
```

- [ ] **Step 2: Inspect the latest GitHub Actions run**

Check the workflow run and combined commit status. A pending run is not a pass.

- [ ] **Step 3: Repair every failure**

For each failed test or build step, reproduce locally, make the smallest production-quality fix, run the affected test, then run the full suite.

- [ ] **Step 4: Repeat until CI is green**

Do not stop at a local pass if GitHub Actions is red. Do not claim completion while any required CI check is failing or pending.

- [ ] **Step 5: Commit each repair separately**

```powershell
git add <verified-files>
git commit -m "fix: resolve CI regression"
```

---

### Task 10: Final Review, PR, and Deployment Verification

**Files:**
- No planned code changes unless verification discovers a defect.

**Interfaces:**
- Consumes: green feature branch.
- Produces: reviewed pull request and verified deployment status.

- [ ] **Step 1: Compare branch against `main`**

Confirm only the intended UI, static-serving, test, and documentation files changed.

- [ ] **Step 2: Run the final full suite**

```powershell
pytest -q
```

Expected: PASS.

- [ ] **Step 3: Open the pull request**

Use a concise title such as `feat: rebuild Barberian UI for strict CSP` and document the CSP root cause, external asset architecture, API preservation, tests, and known non-goals.

- [ ] **Step 4: Verify PR CI**

Wait for required checks and confirm they are green. If any check fails, return to Task 9.

- [ ] **Step 5: Deploy only after CI is green**

Merge/deploy according to the repository's existing workflow; do not bypass failing checks.

- [ ] **Step 6: Verify Render deployment status**

Poll the Barberian Render deployment until it reaches a successful/live state. Do not claim the live UI is fixed while deployment is still queued, building, failed, or unknown.

- [ ] **Step 7: Perform final endpoint smoke checks**

Verify `/api/health`, `/`, `/css/app.css`, and `/js/app.js` return successfully with expected content types and the strict CSP. Confirm the frontend does not depend on inline execution.

- [ ] **Step 8: Report exact verification evidence**

Final report must include branch/PR, final commit SHA, `pytest -q` result, CI result, deployment result, and any explicitly remaining non-goals. Never state that a browser visual check passed unless an actual visual/browser verification was performed.
