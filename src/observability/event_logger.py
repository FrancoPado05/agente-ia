import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable

from src.observability.events import ErrorEvent, ToolCallEvent, TurnEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[TurnEvent | ToolCallEvent | ErrorEvent], Awaitable[None]]


class EventLogger:
    def __init__(self, flush_interval: float = 2.0, batch_size: int = 50):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._flush_interval = flush_interval
        self._batch_size = batch_size
        self._handlers: list[EventHandler] = []
        self._task: asyncio.Task | None = None

    def add_handler(self, handler: EventHandler):
        self._handlers.append(handler)

    async def emit(self, event: TurnEvent | ToolCallEvent | ErrorEvent):
        await self._queue.put(event)

    async def start(self):
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            await self._flush()

    async def _run(self):
        while True:
            await asyncio.sleep(self._flush_interval)
            await self._flush()

    async def _flush(self):
        batch: list = []
        while not self._queue.empty() and len(batch) < self._batch_size:
            try:
                event = self._queue.get_nowait()
                batch.append(event)
            except asyncio.QueueEmpty:
                break

        if not batch:
            return

        for handler in self._handlers:
            try:
                await handler(batch)
            except Exception:
                logger.exception("Event handler failed")
