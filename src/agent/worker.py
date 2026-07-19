import logging
import os

from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.engine import AgentEngine
from src.config.loader import ConfigLoader
from src.config.models import ClientConfig
from src.observability.event_logger import EventLogger
from src.persistence.queries import get_client_config
from src.tools.registry import ToolRegistry
from src.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)


def _make_llm(config: ClientConfig) -> ChatOpenAI:
    return ChatOpenAI(
        model=config.model.model_name,
        temperature=config.model.temperature,
        max_tokens=config.model.max_tokens,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_base_url=os.getenv("OPENROUTER_BASE_URL"),
    )


async def handle_message(
    payload: dict,
    db_session: AsyncSession,
    registry: ToolRegistry,
    whatsapp: WhatsAppClient,
    event_logger: EventLogger,
):
    client_id = payload["client_id"]
    message = payload["message"]

    config_loader = ConfigLoader(fetch_fn=lambda cid: get_client_config(db_session, cid))
    config = await config_loader.load(client_id)

    text = message.get("text", {}).get("body", "")
    phone = message.get("from", "")
    if not text:
        logger.warning("Empty text from %s", phone)
        return

    llm = _make_llm(config)
    engine = AgentEngine(registry, whatsapp)

    async for event in engine.run(config, llm, text, phone):
        await event_logger.emit(event)
