from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "web" / "css" / "app.css").read_text(encoding="utf-8") if (ROOT / "web" / "css" / "app.css").exists() else ""


def test_chat_ui_uses_csp_compatible_external_assets():
    assert '<link rel="stylesheet" href="/css/app.css">' in HTML
    assert '<script type="module" src="/js/app.js"></script>' in HTML
    assert "<style" not in HTML.lower()
    assert "<script>" not in HTML.lower()


def test_chat_ui_has_mobile_first_shell_and_composer():
    for element_id in ("app", "sidebar", "messages", "composer", "mobileMenu", "themeToggle"):
        assert f'id="{element_id}"' in HTML
    assert "--bg:#000000" in CSS


def test_chat_ui_persists_conversations_and_renders_markdown_safely():
    state = (ROOT / "web" / "js" / "state.js").read_text(encoding="utf-8")
    markdown = (ROOT / "web" / "js" / "markdown.js").read_text(encoding="utf-8")
    assert "localStorage" in state
    assert "renderMarkdown" in markdown
    assert "escapeHtml" in markdown


def test_chat_ui_uses_existing_barberian_api_contract():
    api = (ROOT / "web" / "js" / "api.js").read_text(encoding="utf-8")
    assert "'/api/health'" in api
    assert "'/api/chat'" in api
    assert "'/api/events?run_id='" in api
