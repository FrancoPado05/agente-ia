from collections.abc import Awaitable, Callable
from datetime import timedelta


class ClientNotFoundError(Exception):
    pass


class ClientResolver:
    def __init__(
        self,
        lookup_fn: Callable[[str], Awaitable[str | None]],
        cache_ttl: timedelta = timedelta(minutes=15),
    ):
        self._lookup = lookup_fn
        self._cache_ttl = cache_ttl
        self._cache: dict[str, str] = {}
        self._cache_timestamps: dict[str, float] = {}

    async def resolve(self, phone_number_id: str) -> str:
        now = __import__("time").time()
        cached = self._cache.get(phone_number_id)
        ts = self._cache_timestamps.get(phone_number_id, 0)
        if cached and (now - ts) < self._cache_ttl.total_seconds():
            return cached

        client_id = await self._lookup(phone_number_id)
        if not client_id:
            raise ClientNotFoundError(f"No client found for phone_number_id={phone_number_id}")
        self._cache[phone_number_id] = client_id
        self._cache_timestamps[phone_number_id] = now
        return client_id
