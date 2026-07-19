from typing import Any

from langgraph.graph import MessagesState
from pydantic import BaseModel


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result: Any | None = None
    error: str | None = None


class AgentState(MessagesState):
    client_id: str
    conversation_id: str
    system_prompt: str
    enabled_tools: list[str]
    current_tool_call: ToolCallRecord | None = None
    tool_history: list[ToolCallRecord]
