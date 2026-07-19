import logging

import httpx

from src.whatsapp.models import WhatsAppResponse, WhatsAppTextMessage

logger = logging.getLogger(__name__)


class WhatsAppClient:
    BASE_URL = "https://graph.facebook.com"

    def __init__(self, api_token: str, api_version: str = "v22.0"):
        self._token = api_token
        self._api_version = api_version

    async def send_text(self, to: str, body: str, phone_number_id: str) -> WhatsAppResponse:
        message = WhatsAppTextMessage.create(to=to, body=body)
        url = f"{self.BASE_URL}/{self._api_version}/{phone_number_id}/messages"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
                json=message.model_dump(),
            )
            response.raise_for_status()
            return WhatsAppResponse(**response.json())

    async def mark_as_read(self, message_id: str, phone_number_id: str):
        url = f"{self.BASE_URL}/{self._api_version}/{phone_number_id}/messages"
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                },
            )
