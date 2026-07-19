from pydantic import BaseModel


class ToolBinding(BaseModel):
    tool_id: str
    enabled: bool = True


class ModelParams(BaseModel):
    model_name: str = "openai/gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1024


class ClientConfig(BaseModel):
    client_id: str
    phone_number_id: str
    system_prompt: str
    tools: list[ToolBinding] = []
    model: ModelParams = ModelParams()
