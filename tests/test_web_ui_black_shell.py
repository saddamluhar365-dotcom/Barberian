from pathlib import Path


HTML = Path(__file__).parents[1].joinpath("web", "index.html").read_text(encoding="utf-8")


def test_ui_has_black_shell_and_explicit_action_mapping():
    assert "--bg:#000000" in HTML
    assert 'data-action="new-chat"' in HTML
    assert 'data-action="search"' in HTML
    assert 'data-action="settings"' in HTML
    assert 'data-action="attach"' in HTML
    assert 'data-action="send"' in HTML
    assert 'data-action="stop"' in HTML
    assert 'data-action="clear-chat"' in HTML


def test_ui_has_responsive_mobile_and_desktop_contract():
    assert "@media (max-width: 760px)" in HTML
    assert "100dvh" in HTML
    assert "env(safe-area-inset-bottom)" in HTML
    assert "aria-label" in HTML
