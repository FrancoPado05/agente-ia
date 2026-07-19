import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel

from src.queue.interface import QueueInterface
from src.webhook.client_resolver import ClientResolver
from src.webhook.signature import verify_meta_signature

router = APIRouter()


class WebhookPayload(BaseModel):
    object: str
    entry: list[dict]


def depends_resolver(request: Request) -> ClientResolver:
    return request.app.state.client_resolver


def depends_queue(request: Request) -> QueueInterface:
    return request.app.state.queue


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
):
    expected = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and hub_verify_token == expected:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403)


@router.post("/webhook")
async def receive_message(
    payload: WebhookPayload,
    request: Request,
    resolver: Annotated[ClientResolver, Depends(depends_resolver)],
    queue: Annotated[QueueInterface, Depends(depends_queue)],
):
    app_secret = os.getenv("META_APP_SECRET", "")
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not verify_meta_signature(body, sig, app_secret):
        raise HTTPException(status_code=401)

    for entry in payload.entry:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            if not phone_number_id:
                continue
            client_id = await resolver.resolve(phone_number_id)
            messages = value.get("messages", [])
            for msg in messages:
                await queue.enqueue(
                    {
                        "client_id": client_id,
                        "message": msg,
                        "phone_number_id": phone_number_id,
                    }
                )

    return Response(status_code=200)
