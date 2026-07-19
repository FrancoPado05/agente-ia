import pytest

from src.observability.event_logger import EventLogger
from src.observability.events import TurnEvent


@pytest.mark.asyncio
async def test_emit_and_flush():
    received = []

    async def handler(batch):
        received.extend(batch)

    logger = EventLogger(flush_interval=0.1, batch_size=10)
    logger.add_handler(handler)
    await logger.start()

    event = TurnEvent(client_id="c1", conversation_id="conv1", role="assistant", content="hello")
    await logger.emit(event)
    await logger.stop()

    assert len(received) == 1
    assert received[0].content == "hello"
