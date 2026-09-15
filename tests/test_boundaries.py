from barberian.memory import MemoryItem, MemoryStore
from barberian.security import Permission, PermissionPolicy, redact_secret
from barberian.verifier import Verifier


def test_private_memory_never_appears_in_share_safe_view():
    store = MemoryStore()
    store.put(MemoryItem("private", "secret", sensitivity="private", verified=True))
    store.put(MemoryItem("safe", "fact", sensitivity="shared-safe", verified=True))
    assert [item.key for item in store.share_safe()] == ["safe"]


def test_permission_policy_defaults_to_safe_actions():
    policy = PermissionPolicy()
    assert policy.check(Permission.WEB_READ)
    assert not policy.check(Permission.FILE_DELETE)


def test_secret_redaction():
    assert redact_secret("abc123") == "***"
    assert redact_secret("abc123", visible=2) == "ab***"


def test_verifier_reports_failed_checks():
    result = Verifier().verify("x", {"length": lambda value: len(value) > 2})
    assert not result.passed
    assert "length" in result.issues
