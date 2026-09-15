from barberian.usage import UsageTracker


def test_usage_tracker_records_requests_tokens_and_latency():
    tracker = UsageTracker()
    tracker.record("groq", tokens=20, latency_ms=80, success=True)
    tracker.record("groq", tokens=10, latency_ms=40, success=False)
    snapshot = tracker.snapshot("groq")
    assert snapshot["requests"] == 2
    assert snapshot["tokens"] == 30
    assert snapshot["successes"] == 1
    assert snapshot["failures"] == 1
