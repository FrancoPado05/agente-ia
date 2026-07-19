import logging

from src.agent.state import AgentState

logger = logging.getLogger(__name__)


async def responder_node(state: AgentState) -> dict:
    last_msg = state.messages[-1]
    return {
        "messages": [last_msg],
    }
