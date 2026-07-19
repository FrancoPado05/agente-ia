import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage

from src.agent.state import AgentState

logger = logging.getLogger(__name__)


async def interpret_node(state: AgentState, llm: BaseChatModel) -> dict:
    system = SystemMessage(content=state.system_prompt)
    response = await llm.ainvoke([system] + state.messages)
    return {"messages": [response]}
