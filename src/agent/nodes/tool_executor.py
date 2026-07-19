import logging

from src.agent.state import AgentState, ToolCallRecord
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


async def tool_executor_node(state: AgentState, registry: ToolRegistry) -> dict:
    last_msg = state.messages[-1]
    if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return {}

    records = []
    for tc in last_msg.tool_calls:
        tool_name = tc.get("name", "")
        if tool_name not in state.enabled_tools:
            logger.warning("Tool %s not enabled for client %s", tool_name, state.client_id)
            continue

        tool = registry.get(tool_name)
        if not tool:
            logger.error("Tool %s not found in registry", tool_name)
            continue

        result = await tool.arun(**tc.get("args", {}))
        record = ToolCallRecord(
            tool_name=tool_name,
            arguments=tc.get("args", {}),
            result=result,
        )
        records.append(record)

    return {
        "tool_history": state.tool_history + records,
        "current_tool_call": records[-1] if records else None,
    }
