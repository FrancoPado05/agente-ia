import pytest

from src.config.loader import ConfigLoader
from src.config.models import ClientConfig


@pytest.mark.asyncio
async def test_load_caches():
    call_count = 0

    async def fetch(cid: str) -> ClientConfig | None:
        nonlocal call_count
        call_count += 1
        return ClientConfig(client_id=cid, phone_number_id="123", system_prompt="test")

    loader = ConfigLoader(fetch_fn=fetch)
    c1 = await loader.load("c1")
    c2 = await loader.load("c1")
    assert call_count == 1
    assert c1.client_id == "c1"
    assert c2.client_id == "c1"


@pytest.mark.asyncio
async def test_invalidate_clears_cache():
    call_count = 0

    async def fetch(cid: str) -> ClientConfig | None:
        nonlocal call_count
        call_count += 1
        return ClientConfig(client_id=cid, phone_number_id="123", system_prompt="test")

    loader = ConfigLoader(fetch_fn=fetch)
    await loader.load("c1")
    loader.invalidate("c1")
    await loader.load("c1")
    assert call_count == 2
