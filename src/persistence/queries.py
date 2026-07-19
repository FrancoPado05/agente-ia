from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.models import ClientConfig, ModelParams, ToolBinding


async def get_client_id_by_phone(session: AsyncSession, phone_number_id: str) -> str | None:
    result = await session.execute(
        text("SELECT id FROM clients WHERE phone_number_id = :phone AND is_active = TRUE"),
        {"phone": phone_number_id},
    )
    row = result.one_or_none()
    return row[0] if row else None


async def get_client_config(session: AsyncSession, client_id: str) -> ClientConfig | None:
    result = await session.execute(
        text("""
            SELECT id, phone_number_id, system_prompt, model_name, temperature, max_tokens
            FROM clients
            WHERE id = :cid AND is_active = TRUE
        """),
        {"cid": client_id},
    )
    row = result.one_or_none()
    if not row:
        return None

    tools_result = await session.execute(
        text("SELECT tool_id FROM client_tools WHERE client_id = :cid AND enabled = TRUE"),
        {"cid": client_id},
    )
    tools = [ToolBinding(tool_id=r[0]) for r in tools_result]

    return ClientConfig(
        client_id=row[0],
        phone_number_id=row[1],
        system_prompt=row[2],
        model=ModelParams(
            model_name=row[3],
            temperature=row[4],
            max_tokens=row[5],
        ),
        tools=tools,
    )
