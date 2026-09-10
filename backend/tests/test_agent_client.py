import pytest

from app.agent.client import OpenAIClient, get_llm_client
from app.core.config import Settings
from app.core.errors import LLMNotConfigured
from tests.fakes import FakeLLMClient


def test_fake_client_records_inputs():
    fake = FakeLLMClient(response="hello")
    assert fake.complete("sys", "usr") == "hello"
    assert fake.last_system == "sys"
    assert fake.last_user == "usr"


def test_get_llm_client_builds_openai_client(monkeypatch):
    monkeypatch.setattr("app.agent.client.get_settings", lambda: Settings(llm_api_key="sk-test"))
    client = get_llm_client()
    assert isinstance(client, OpenAIClient)
    assert hasattr(client, "complete")


def test_get_llm_client_raises_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.agent.client.get_settings", lambda: Settings(llm_api_key=""))
    with pytest.raises(LLMNotConfigured):
        get_llm_client()
