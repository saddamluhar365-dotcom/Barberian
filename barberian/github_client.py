"""GitHub REST client using runtime-only credentials."""

import json
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin


class GitHubAPI:
    def __init__(self, token: str, *, base_url: str = "https://api.github.com/", timeout: float = 30.0) -> None:
        if not token:
            raise ValueError("GitHub token is required")
        self.token = token
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = max(1.0, float(timeout))

    def build_request(self, path: str, *, method: str = "GET", body: dict | None = None):
        url = urljoin(self.base_url, path.lstrip("/"))
        data = json.dumps(body).encode() if body is not None else None
        return request.Request(url, data=data, method=method, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})

    def call(self, path: str, *, method: str = "GET", body: dict | None = None) -> dict:
        try:
            with request.urlopen(self.build_request(path, method=method, body=body), timeout=self.timeout) as response:
                raw = response.read().decode()
        except HTTPError as exc:
            raise RuntimeError(f"GitHub HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"GitHub network error: {exc.reason}") from exc
        return json.loads(raw) if raw else {}

    def repository(self, owner: str, repo: str) -> dict:
        return self.call(f"repos/{owner}/{repo}")

    def issues(self, owner: str, repo: str) -> list[dict]:
        return self.call(f"repos/{owner}/{repo}/issues?state=open")

    def pull_requests(self, owner: str, repo: str) -> list[dict]:
        return self.call(f"repos/{owner}/{repo}/pulls?state=open")
