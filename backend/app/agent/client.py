from typing import Protocol

from openai import BadRequestError, OpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import get_settings
from app.core.errors import LLMNotConfigured


class LLMClient(Protocol):
    def complete(self, system: str, user: str, *, json_object: bool = False) -> str: ...


class OpenAIClient:
    """Provider-agnostic OpenAI-compatible chat client."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        # A hung provider must not hold a request thread open indefinitely.
        self._client = OpenAI(
            base_url=base_url, api_key=api_key or "not-set", timeout=60.0, max_retries=2
        )
        self._model = model

    def complete(self, system: str, user: str, *, json_object: bool = False) -> str:
        """`json_object` asks the provider to guarantee parseable JSON. Not every
        OpenAI-compatible endpoint supports response_format, so a rejection falls back to a
        plain call — the caller parses defensively either way."""
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        def _plain():
            return self._client.chat.completions.create(
                model=self._model, messages=messages, temperature=0
            )

        if not json_object:
            resp = _plain()
        else:
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=0,
                    response_format={"type": "json_object"},
                )
            except BadRequestError:
                resp = _plain()
        if not resp.choices:
            return ""
        return resp.choices[0].message.content or ""


def get_llm_client() -> LLMClient:
    s = get_settings()
    if not s.llm_api_key.strip():
        raise LLMNotConfigured(
            "LLM is not configured. Set LLM_API_KEY (and LLM_BASE_URL / LLM_MODEL) "
            "in backend/.env to enable Ask Canopy and Generate Memo."
        )
    return OpenAIClient(s.llm_base_url, s.llm_api_key, s.llm_model)
