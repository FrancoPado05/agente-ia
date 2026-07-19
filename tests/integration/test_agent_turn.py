from src.tools.builtin.get_weather import GetWeather
from src.tools.registry import ToolRegistry


def test_tool_registry_integration():
    registry = ToolRegistry()
    registry.register(GetWeather())

    assert "get_weather" in registry
    tool = registry.get("get_weather")
    assert tool is not None
    assert tool.name == "get_weather"
    schema = tool.to_openai_tool()
    assert schema["function"]["name"] == "get_weather"
