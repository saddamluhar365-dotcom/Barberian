from datetime import datetime, timezone

from barberian.automation import Automation, AutomationScheduler


def test_scheduler_supports_hourly_interval_schedule():
    automation = Automation("1", "hourly", "do it", "every 1h")
    now = datetime(2026, 9, 15, 10, 30, tzinfo=timezone.utc)
    assert AutomationScheduler().next_run(automation, now).hour == 11
