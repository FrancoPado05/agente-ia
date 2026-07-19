import asyncio
import logging
from collections.abc import Awaitable, Callable

from src.queue.interface import QueueInterface

logger = logging.getLogger(__name__)


async def run_worker(
    queue: QueueInterface,
    handler: Callable[[dict], Awaitable[None]],
    shutdown_event: asyncio.Event,
):
    await queue.start_consumer(handler)
    await shutdown_event.wait()
    await queue.stop()
