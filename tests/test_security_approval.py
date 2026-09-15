from barberian.security import ApprovalManager, Permission, PermissionPolicy


def test_destructive_permission_requires_explicit_approval():
    policy = PermissionPolicy()
    approvals = ApprovalManager()
    token = approvals.issue(Permission.FILE_DELETE)
    assert not policy.check(Permission.FILE_DELETE)
    assert approvals.consume(token, Permission.FILE_DELETE)
    assert not approvals.consume(token, Permission.FILE_DELETE)
