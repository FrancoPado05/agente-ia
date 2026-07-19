from src.tools.builtin.get_weather import GetWeather
from src.tools.registry import ToolRegistry


def test_register_and_get():
    registry = ToolRegistry()
    tool = GetWeather()
    registry.register(tool)
    assert registry.get("get_weather") is tool


def test_get_enabled_filters_unknown():
    registry = ToolRegistry()
    registry.register(GetWeather())
    tools = registry.get_enabled(["get_weather", "nonexistent"])
    names = [t["function"]["name"] for t in tools]
    assert names == ["get_weather"]


def test_contains():
    registry = ToolRegistry()
    registry.register(GetWeather())
    assert "get_weather" in registry
    assert "unknown" not in registry
