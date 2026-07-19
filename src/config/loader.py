from collections.abc import Awaitable, Callable
from datetime import timedelta

from src.config.models import ClientConfig


class ConfigLoader:
    def __init__(
        self,
        fetch_fn: Callable[[str], Awaitable[ClientConfig | None]],
        cache_ttl: timedelta = timedelta(minutes=5),
    ):
        self._fetch = fetch_fn
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[ClientConfig, float]] = {}

    async def load(self, client_id: str) -> ClientConfig:
        now = __import__("time").time()
        cached, ts = self._cache.get(client_id, (None, 0))
        if cached and (now - ts) < self._cache_ttl.total_seconds():
            return cached

        config = await self._fetch(client_id)
        if not config:
            raise ValueError(f"Config not found for client_id={client_id}")
        self._cache[client_id] = (config, now)
        return config

    def invalidate(self, client_id: str):
        self._cache.pop(client_id, None)
