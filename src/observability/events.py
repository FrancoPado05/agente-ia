from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TurnEvent(BaseModel):
    client_id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime = Field(default_factory=_utcnow)


class ToolCallEvent(BaseModel):
    client_id: str
    conversation_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: Any = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=_utcnow)


class ErrorEvent(BaseModel):
    client_id: str
    conversation_id: str
    error_type: str
    message: str
    details: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=_utcnow)
