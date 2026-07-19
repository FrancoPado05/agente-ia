from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, StateGraph

from src.agent.nodes.interpreter import interpret_node
from src.agent.nodes.responder import responder_node
from src.agent.nodes.tool_executor import tool_executor_node
from src.agent.state import AgentState
from src.tools.registry import ToolRegistry


def build_graph(llm: BaseChatModel, registry: ToolRegistry) -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("interpret", lambda s: interpret_node(s, llm))
    builder.add_node("execute_tool", lambda s: tool_executor_node(s, registry))
    builder.add_node("respond", responder_node)

    builder.set_entry_point("interpret")

    def has_tool_call(state: AgentState) -> str:
        last = state.messages[-1] if state.messages else None
        if last and hasattr(last, "tool_calls") and last.tool_calls:
            return "execute_tool"
        return "respond"

    builder.add_conditional_edges(
        "interpret",
        has_tool_call,
        {
            "execute_tool": "execute_tool",
            "respond": "respond",
        },
    )
    builder.add_edge("execute_tool", "interpret")
    builder.add_edge("respond", END)

    return builder.compile()
