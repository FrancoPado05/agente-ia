from typing import Any

from src.tools.base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_enabled(self, tool_ids: list[str]) -> list[dict[str, Any]]:
        return [self._tools[tid].to_openai_tool() for tid in tool_ids if tid in self._tools]

    def __contains__(self, name: str) -> bool:
        return name in self._tools
