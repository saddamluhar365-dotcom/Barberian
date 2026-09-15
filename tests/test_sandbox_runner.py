import sys

from barberian.sandbox import Sandbox


def test_sandbox_runs_process_with_output_capture():
    result = Sandbox().run([sys.executable, "-c", "print('ok')"])
    assert result.returncode == 0
    assert result.stdout.strip() == "ok"


def test_sandbox_rejects_empty_command():
    try:
        Sandbox().run([])
    except ValueError:
        return
    raise AssertionError("empty command must fail")
