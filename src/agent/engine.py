import logging
import uuid
from collections.abc import AsyncGenerator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph.graph import CompiledGraph

from src.agent.graph import build_graph
from src.agent.state import AgentState
from src.config.models import ClientConfig
from src.observability.events import ToolCallEvent, TurnEvent
from src.tools.registry import ToolRegistry
from src.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)


class AgentEngine:
    def __init__(self, registry: ToolRegistry, whatsapp: WhatsAppClient):
        self._registry = registry
        self._whatsapp = whatsapp
        self._graph_cache: dict[str, CompiledGraph] = {}

    def _get_graph(self, config: ClientConfig, llm: BaseChatModel) -> CompiledGraph:
        key = config.client_id
        if key not in self._graph_cache:
            self._graph_cache[key] = build_graph(llm, self._registry)
        return self._graph_cache[key]

    async def run(
        self,
        config: ClientConfig,
        llm: BaseChatModel,
        user_message: str,
        phone_number: str,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[TurnEvent | ToolCallEvent]:
        conv_id = conversation_id or str(uuid.uuid4())
        graph = self._get_graph(config, llm)

        initial_state = AgentState(
            messages=[HumanMessage(content=user_message)],
            client_id=config.client_id,
            conversation_id=conv_id,
            system_prompt=config.system_prompt,
            enabled_tools=[t.tool_id for t in config.tools],
        )

        async for event in graph.astream_events(initial_state, version="v2"):
            if event["event"] == "on_chat_model_end":
                msg = event["data"]["output"]
                text = msg.content if hasattr(msg, "content") else str(msg)
                yield TurnEvent(
                    client_id=config.client_id,
                    conversation_id=conv_id,
                    role="assistant",
                    content=text,
                )

            if event["event"] == "on_tool_start":
                tc = event["data"].get("input", {})
                yield ToolCallEvent(
                    client_id=config.client_id,
                    conversation_id=conv_id,
                    tool_name=tc.get("name", "unknown"),
                    arguments=tc.get("args", {}),
                )

        response = graph.get_state(initial_state.config).values.get("messages", [])
        if response:
            last = response[-1]
            text = last.content if hasattr(last, "content") else str(last)
            await self._whatsapp.send_text(phone_number, text)
