import time
import urllib.error
import urllib.request


def wait_for_url(url: str, timeout: float = 3.0):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            return urllib.request.urlopen(url, timeout=0.5)
        except (urllib.error.URLError, ConnectionError) as exc:
            last_error = exc
            time.sleep(0.05)
    raise last_error or RuntimeError(f"server did not start: {url}")
