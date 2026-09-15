# Barberian UI Rebuild Design

## Goal
Replace the current monolithic inline frontend with a predictable, production-quality Vanilla HTML/CSS/JavaScript interface that renders correctly under the existing strict Content Security Policy and preserves the current Barberian API contract.

## Problem
The current `web/index.html` embeds a large `<style>` block and a large inline `<script>`, while `app.py` sends a strict CSP that does not permit inline styles or scripts. This can cause the browser to reject the frontend behavior/styles and fall back toward unstyled or partially functional markup. The frontend also concentrates layout, state, API, history, Markdown rendering, and interaction logic in one file, making regressions difficult to isolate.

## Architecture
Use a static frontend with clear responsibilities:

- `web/index.html`: semantic DOM structure only; references external assets.
- `web/css/app.css`: complete responsive visual system and layout.
- `web/js/app.js`: application bootstrap and orchestration.
- `web/js/api.js`: health/chat/events API access.
- `web/js/state.js`: chat/settings state and persistence boundaries.
- `web/js/chat.js`: message lifecycle, send/stop, rendering hooks.
- `web/js/history.js`: local chat history and search.
- `web/js/markdown.js`: safe Markdown-to-HTML rendering and escaping.
- `web/js/ui.js`: sidebar, mobile drawer, settings, composer, toasts.

No third-party frontend framework or CDN is required. All executable frontend code and styling are same-origin external files so the existing strict CSP remains effective.

## Visual Contract

- Pure black AMOLED page background.
- Desktop: fixed-width left navigation and full-height main chat surface.
- Mobile: navigation becomes a drawer with overlay; chat remains full viewport width.
- Header is compact and stable; no overlapping controls.
- Welcome state is centered in the usable chat area and does not collide with the composer.
- Messages use consistent max width, spacing, typography, avatars, code blocks, and action rows.
- Composer is anchored to the bottom and accounts for mobile safe-area insets.
- Controls have visible hover/focus/disabled states and accessible labels.
- No gradients, browser-default form controls, giant empty cards, or decorative controls without an action.
- Every visible interactive control has a deterministic action or is explicitly status-only.

## Functional Contract

Preserve these existing endpoints:

- `GET /api/health`
- `GET /api/status`
- `GET /api/providers`
- `GET /api/models`
- `GET /api/capabilities`
- `GET /api/mcp`
- `GET /api/skills`
- `GET /api/integrations`
- `GET /api/tasks`
- `GET /api/events?run_id=...`
- `POST /api/chat` with `{\"message\":\"...\"}`
- `POST /api/tasks` with `{\"message\":\"...\"}`

The frontend must handle success, API errors, network failures, cancellation, empty responses, and loading states without breaking the layout.

## Security

- Keep the strict CSP; do not add `unsafe-inline` merely to make the UI work.
- Keep HTML escaping for user/agent content before rendering.
- External links generated from Markdown must use safe HTTP(S) handling and `noopener noreferrer`.
- Do not expose provider secrets, runtime environment variables, or internal stack traces in the UI.
- Static assets must be served with correct MIME types and cache policy.

## Testing

Add deterministic tests that verify:

1. index references external CSS and JavaScript files.
2. index contains no inline `<style>` or executable inline `<script>` blocks.
3. required DOM IDs/actions remain present.
4. responsive and safe-area CSS contract exists.
5. CSP does not require inline execution.
6. Python serves `/`, CSS, and JS with correct content types.
7. existing API health behavior remains intact.
8. full pytest suite passes.

## Non-Goals

- Do not replace the Python agent runtime.
- Do not change provider routing or credentials.
- Do not introduce React/Vue solely for presentation.
- Do not claim file upload support unless a backend upload API exists.
- Do not claim true live streaming unless the frontend consumes the event stream incrementally.
