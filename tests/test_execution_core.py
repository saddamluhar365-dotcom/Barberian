from barberian.core.execution import ExecutionEngine, Task, TaskState


def test_task_graph_runs_dependencies_in_order():
    events = []
    engine = ExecutionEngine()
    engine.add_task(Task("research", lambda: events.append("research") or "sources"))
    engine.add_task(Task("write", lambda: events.append("write") or "draft", dependencies=("research",)))

    result = engine.run()

    assert result.status == TaskState.SUCCEEDED
    assert events == ["research", "write"]
    assert result.outputs["write"] == "draft"


def test_failed_task_does_not_execute_dependents():
    events = []
    engine = ExecutionEngine()
    engine.add_task(Task("broken", lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
    engine.add_task(Task("after", lambda: events.append("after"), dependencies=("broken",)))

    result = engine.run()

    assert result.status == TaskState.FAILED
    assert events == []
    assert result.errors["broken"] == "boom"


def test_parallel_ready_tasks_are_supported():
    engine = ExecutionEngine(max_workers=2)
    engine.add_task(Task("a", lambda: "A"))
    engine.add_task(Task("b", lambda: "B"))
    result = engine.run()
    assert result.outputs == {"a": "A", "b": "B"}
