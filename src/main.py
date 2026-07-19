import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.observability.event_logger import EventLogger
from src.tools.builtin.get_weather import GetWeather
from src.tools.registry import ToolRegistry
from src.webhook.router import router as webhook_router
from src.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = ToolRegistry()
    registry.register(GetWeather())
    app.state.tool_registry = registry

    event_logger = EventLogger()
    await event_logger.start()
    app.state.event_logger = event_logger

    app.state.whatsapp_client = WhatsAppClient(api_token="TODO")

    yield

    await event_logger.stop()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(webhook_router)
    return app


app = create_app()
