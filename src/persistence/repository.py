from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from src.persistence.models import Conversation, MessageRecord, ToolCallRecord


class ConversationRepository:
    def __init__(self, conn: AsyncConnection):
        self._conn = conn

    async def create_conversation(self, conv: Conversation) -> str:
        result = await self._conn.execute(
            text("""
                INSERT INTO conversations (client_id, phone_number, status)
                VALUES (:client_id, :phone_number, :status)
                RETURNING id
            """),
            {
                "client_id": conv.client_id,
                "phone_number": conv.phone_number,
                "status": conv.status,
            },
        )
        row = result.one()
        return str(row[0])

    async def list_conversations(
        self, client_id: str, limit: int = 50, offset: int = 0
    ) -> Sequence[Conversation]:
        result = await self._conn.execute(
            text("""
                SELECT id, client_id, phone_number, status, created_at, updated_at
                FROM conversations
                WHERE client_id = :client_id
                ORDER BY updated_at DESC
                LIMIT :lim OFFSET :off
            """),
            {"client_id": client_id, "lim": limit, "off": offset},
        )
        return [Conversation(**row._mapping) for row in result]

    async def add_message(self, msg: MessageRecord) -> str:
        result = await self._conn.execute(
            text("""
                INSERT INTO messages (client_id, conversation_id, role, content, metadata)
                VALUES (:client_id, :conversation_id, :role, :content, :metadata)
                RETURNING id
            """),
            {
                "client_id": msg.client_id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata,
            },
        )
        row = result.one()
        return str(row[0])

    async def get_messages(self, client_id: str, conversation_id: str) -> Sequence[MessageRecord]:
        result = await self._conn.execute(
            text("""
                SELECT id, client_id, conversation_id, role, content, metadata, created_at
                FROM messages
                WHERE client_id = :client_id AND conversation_id = :conversation_id
                ORDER BY created_at ASC
            """),
            {"client_id": client_id, "conversation_id": conversation_id},
        )
        return [MessageRecord(**row._mapping) for row in result]

    async def add_tool_call(self, tc: ToolCallRecord) -> str:
        result = await self._conn.execute(
            text("""
                INSERT INTO tool_calls
                    (client_id, conversation_id, tool_name, arguments, result, error)
                VALUES (:client_id, :conversation_id, :tool_name, :arguments, :result, :error)
                RETURNING id
            """),
            {
                "client_id": tc.client_id,
                "conversation_id": tc.conversation_id,
                "tool_name": tc.tool_name,
                "arguments": tc.arguments,
                "result": tc.result,
                "error": tc.error,
            },
        )
        row = result.one()
        return str(row[0])
