from pathlib import Path


HTML = Path(__file__).parents[1].joinpath("web", "index.html").read_text(encoding="utf-8")


def test_chat_ui_has_mobile_first_shell_and_composer():
    assert 'id="app"' in HTML
    assert 'id="sidebar"' in HTML
    assert 'id="messages"' in HTML
    assert 'id="composer"' in HTML
    assert 'id="mobileMenu"' in HTML
    assert 'id="themeToggle"' in HTML


def test_chat_ui_persists_conversations_and_renders_markdown_safely():
    assert "localStorage" in HTML
    assert "renderMarkdown" in HTML
    assert "copyMessage" in HTML or 'class="copy"' in HTML or "className='copy'" in HTML
    assert "escapeHtml" in HTML or "function esc" in HTML


def test_chat_ui_uses_existing_barberian_api_contract():
    assert "'/api/health'" in HTML
    assert "'/api/chat'" in HTML
    assert "'/api/events?run_id='" in HTML
