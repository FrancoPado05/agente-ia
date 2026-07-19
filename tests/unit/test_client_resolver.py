import pytest

from src.webhook.client_resolver import ClientNotFoundError, ClientResolver


@pytest.mark.asyncio
async def test_resolve_returns_client_id():
    async def lookup(_phone: str) -> str | None:
        return "client_1" if _phone == "123" else None

    resolver = ClientResolver(lookup_fn=lookup)
    result = await resolver.resolve("123")
    assert result == "client_1"


@pytest.mark.asyncio
async def test_resolve_raises_on_unknown():
    async def lookup(_phone: str) -> str | None:
        return None

    resolver = ClientResolver(lookup_fn=lookup)
    with pytest.raises(ClientNotFoundError):
        await resolver.resolve("999")


@pytest.mark.asyncio
async def test_resolve_caches_result():
    call_count = 0

    async def lookup(_phone: str) -> str | None:
        nonlocal call_count
        call_count += 1
        return "client_1"

    resolver = ClientResolver(lookup_fn=lookup)
    await resolver.resolve("123")
    await resolver.resolve("123")
    assert call_count == 1
