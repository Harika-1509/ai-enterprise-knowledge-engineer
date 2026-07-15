import json
from typing import Iterator

import httpx

from app.services.llm.base_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str | None = None):
        from app.core.config import settings
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = model

    def generate(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800) -> str:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model, "messages": messages, "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()

    def generate_stream(
        self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800
    ) -> Iterator[str]:
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": self.model, "messages": messages, "stream": True,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content