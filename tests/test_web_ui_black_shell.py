from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "web" / "css" / "app.css").read_text(encoding="utf-8") if (ROOT / "web" / "css" / "app.css").exists() else ""


def test_ui_has_black_shell_and_explicit_action_mapping():
    assert "--bg:#000000" in CSS
    for action in ("new-chat", "search", "settings", "attach", "send", "stop", "clear-chat"):
        assert f'data-action="{action}"' in HTML


def test_ui_has_responsive_mobile_and_desktop_contract():
    assert "@media (max-width: 760px)" in CSS
    assert "100dvh" in CSS
    assert "env(safe-area-inset-bottom)" in CSS
    assert "aria-label" in HTML
