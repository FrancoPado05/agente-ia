from typing import Any

from src.tools.base import BaseTool


class GetWeather(BaseTool):
    name = "get_weather"
    description = "Get current weather for a city"

    async def arun(self, **kwargs: Any) -> Any:
        city = kwargs.get("city", "")
        return {"city": city, "temperature": 22, "condition": "sunny"}

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        }
