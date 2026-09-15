from barberian.github_client import GitHubAPI


def test_github_api_builds_authenticated_request_without_leaking_token():
    client = GitHubAPI("secret-token")
    req = client.build_request("repos/octo/repo")
    assert req.full_url.endswith("repos/octo/repo")
    assert req.headers["Authorization"] == "Bearer secret-token"
    assert "secret-token" not in repr(req.full_url)
