from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import create_app


@pytest.fixture
def app():
    _app = create_app()
    _app.state.client_resolver = AsyncMock()
    _app.state.client_resolver.resolve.return_value = "test_client"
    _app.state.queue = AsyncMock()
    return _app


@pytest.mark.asyncio
async def test_webhook_get_verify(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "TODO_SET_VERIFY_TOKEN",
                "hub.challenge": "12345",
            },
        )
    assert resp.status_code == 200
    assert resp.text == "12345"
