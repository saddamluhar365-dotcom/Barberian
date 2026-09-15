from barberian.events import EventBus, ExecutionEvent


def test_event_bus_publishes_and_replays_events():
    bus = EventBus(max_events=10)
    event = ExecutionEvent(run_id="r1", event_type="started", payload={"step": "plan"})
    bus.publish(event)
    assert bus.replay("r1")[0].payload["step"] == "plan"
