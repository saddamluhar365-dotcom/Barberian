from barberian.agent_loop import AgentLoop


def test_agent_loop_records_plan_execution_and_verification():
    loop = AgentLoop(executor=lambda step: "done")
    result = loop.run("do a task")
    assert result.success
    assert result.steps[0].status == "SUCCEEDED"
    assert result.steps[0].output == "done"
