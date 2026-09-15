from barberian.orchestration import RunState, idempotency_key


def test_idempotency_key_is_deterministic():
    assert idempotency_key("op", {"b": 2, "a": 1}) == idempotency_key("op", {"a": 1, "b": 2})


def test_run_state_persists_checkpoint_and_attempt_count():
    state = RunState("run-1")
    state.checkpoint("step-1", "SUCCEEDED", {"value": 1})
    state.attempts["step-1"] = state.attempts.get("step-1", 0) + 1
    assert state.checkpoints["step-1"].output == {"value": 1}
    assert state.attempts["step-1"] == 1
