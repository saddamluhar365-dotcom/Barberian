from pathlib import Path

from barberian.security_gate import SecurityGate, Severity


def test_secret_assignment_without_quotes_is_detected(tmp_path: Path):
    (tmp_path / "config.py").write_text("API_KEY=sk-123456789012345678901234\n", encoding="utf-8")
    report = SecurityGate(tmp_path).audit()
    assert any(f.category == "secrets" and f.severity == Severity.CRITICAL for f in report.findings)


def test_comments_do_not_create_secret_finding(tmp_path: Path):
    (tmp_path / "docs.py").write_text("# API_KEY=sk-123456789012345678901234\n", encoding="utf-8")
    report = SecurityGate(tmp_path).audit()
    assert not any(f.category == "secrets" for f in report.findings)
