from pydantic import BaseModel


class WhatsAppTextMessage(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "text"
    text: dict

    @classmethod
    def create(cls, to: str, body: str) -> "WhatsAppTextMessage":
        return cls(to=to, text={"body": body})


class WhatsAppResponse(BaseModel):
    messaging_product: str
    contacts: list[dict] = []
    messages: list[dict] = []
