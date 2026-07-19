import logging
import uuid
from collections.abc import AsyncGenerator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.config.models import ClientConfig
from src.observability.events import ToolCallEvent, TurnEvent
from src.tools.registry import ToolRegistry
from src.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)


class AgentEngine:
    def __init__(self, registry: ToolRegistry, whatsapp: WhatsAppClient):
        self._registry = registry
        self._whatsapp = whatsapp

    async def run(
        self,
        config: ClientConfig,
        llm: BaseChatModel,
        user_message: str,
        phone_number: str,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[TurnEvent | ToolCallEvent]:
        conv_id = conversation_id or str(uuid.uuid4())

        system = SystemMessage(content=config.system_prompt)
        human = HumanMessage(content=user_message)

        response = await llm.ainvoke([system, human])
        reply = response.content if hasattr(response, "content") else str(response)

        event = TurnEvent(
            client_id=config.client_id,
            conversation_id=conv_id,
            role="assistant",
            content=reply,
        )
        yield event

        await self._whatsapp.send_text(
            to=phone_number,
            body=reply,
            phone_number_id=config.phone_number_id,
        )
