from pathlib import Path

from barberian.security_gate import SecurityGate, Severity


def test_security_gate_detects_hardcoded_secret_and_shell_risk(tmp_path: Path):
    (tmp_path / "bad.py").write_text('API_KEY = "sk-123456789012345678901234"\nsubprocess.run(user_input, shell=True)\n', encoding="utf-8")
    report = SecurityGate(tmp_path).audit()
    severities = {finding.severity for finding in report.findings}
    assert Severity.CRITICAL in severities or Severity.HIGH in severities
    assert any("secret" in finding.title.lower() for finding in report.findings)


def test_security_gate_passes_clean_project(tmp_path: Path):
    (tmp_path / "app.py").write_text('print("hello")\n', encoding="utf-8")
    report = SecurityGate(tmp_path).audit()
    assert report.gate.value == "SECURITY GATE: PASS"


def test_security_gate_never_leaks_secret_value(tmp_path: Path):
    secret = "sk-test-abcdefghijklmnopqrstuvwxyz123456"
    (tmp_path / ".env").write_text(f"OPENAI_API_KEY={secret}\n", encoding="utf-8")
    report = SecurityGate(tmp_path).audit()
    assert secret not in report.to_dict().__repr__()
