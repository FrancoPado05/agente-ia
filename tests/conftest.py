import pytest

from src.config.models import ClientConfig, ModelParams, ToolBinding
from src.tools.builtin.get_weather import GetWeather
from src.tools.registry import ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(GetWeather())
    return r


@pytest.fixture
def sample_config() -> ClientConfig:
    return ClientConfig(
        client_id="test_client_1",
        phone_number_id="123456789",
        system_prompt="You are a helpful assistant for test_client_1.",
        tools=[ToolBinding(tool_id="get_weather")],
        model=ModelParams(),
    )
