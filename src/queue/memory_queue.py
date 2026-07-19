import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from src.queue.interface import QueueInterface

logger = logging.getLogger(__name__)


class MemoryQueue(QueueInterface):
    def __init__(self):
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._consumer_task: asyncio.Task | None = None

    async def enqueue(self, payload: dict[str, Any]) -> None:
        await self._queue.put(payload)

    async def dequeue(self) -> dict[str, Any] | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except TimeoutError:
            return None

    async def start_consumer(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        async def _loop():
            while True:
                payload = await self._queue.get()
                try:
                    await handler(payload)
                except Exception:
                    logger.exception("Consumer handler failed")
                finally:
                    self._queue.task_done()

        self._consumer_task = asyncio.create_task(_loop())

    async def stop(self) -> None:
        if self._consumer_task:
            self._consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._consumer_task
