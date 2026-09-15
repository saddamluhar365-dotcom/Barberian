"""Worker entry point for long-running jobs; durable queue backends plug in here."""

import time


def run_worker() -> None:
    while True:
        # Queue integration is intentionally isolated from the HTTP process.
        time.sleep(5)


if __name__ == "__main__":
    run_worker()
