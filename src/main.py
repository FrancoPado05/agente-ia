import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from src.agent.worker import handle_message
from src.observability.event_logger import EventLogger
from src.persistence.database import close_engine, get_session, init_engine
from src.persistence.queries import get_client_id_by_phone
from src.queue.memory_queue import MemoryQueue
from src.tools.builtin.get_weather import GetWeather
from src.tools.registry import ToolRegistry
from src.webhook.router import router as webhook_router
from src.whatsapp.client import WhatsAppClient

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting agente-ia")

    await init_engine()
    logger.info("Database engine initialized")

    registry = ToolRegistry()
    registry.register(GetWeather())
    app.state.tool_registry = registry

    event_logger = EventLogger()
    await event_logger.start()
    app.state.event_logger = event_logger

    whatsapp = WhatsAppClient()
    app.state.whatsapp_client = whatsapp

    queue = MemoryQueue()

    async def resolve_client(phone_number_id: str) -> str | None:
        async with get_session() as session:
            return await get_client_id_by_phone(session, phone_number_id)

    from src.webhook.client_resolver import ClientResolver

    resolver = ClientResolver(lookup_fn=resolve_client)
    app.state.client_resolver = resolver

    async def consumer(payload: dict):
        async with get_session() as session:
            await handle_message(payload, session, registry, whatsapp, event_logger)

    await queue.start_consumer(consumer)
    app.state.queue = queue

    logger.info("Startup complete")
    yield

    await queue.stop()
    await event_logger.stop()
    await close_engine()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(webhook_router)
    return app


app = create_app()
