from collections.abc import Awaitable, Callable
from typing import Any, Protocol


class QueueInterface(Protocol):
    async def enqueue(self, payload: dict[str, Any]) -> None: ...

    async def dequeue(self) -> dict[str, Any] | None: ...

    async def start_consumer(
        self, handler: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None: ...

    async def stop(self) -> None: ...
