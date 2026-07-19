from datetime import datetime

from pydantic import BaseModel


class MessageRecord(BaseModel):
    id: str = ""
    client_id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict | None = None
    created_at: datetime | None = None


class ToolCallRecord(BaseModel):
    id: str = ""
    client_id: str
    conversation_id: str
    tool_name: str
    arguments: dict
    result: str | None = None
    error: str | None = None
    created_at: datetime | None = None


class Conversation(BaseModel):
    id: str = ""
    client_id: str
    phone_number: str
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None
