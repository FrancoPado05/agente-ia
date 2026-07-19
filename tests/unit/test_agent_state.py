from src.agent.state import AgentState, ToolCallRecord


def test_agent_state_defaults():
    state = AgentState(
        messages=[],
        client_id="c1",
        conversation_id="conv1",
        system_prompt="Hello",
        enabled_tools=["t1"],
        tool_history=[],
    )
    assert state["tool_history"] == []
    assert state.get("current_tool_call") is None


def test_tool_call_record():
    record = ToolCallRecord(tool_name="get_weather", arguments={"city": "BA"})
    assert record.tool_name == "get_weather"
    assert record.result is None
