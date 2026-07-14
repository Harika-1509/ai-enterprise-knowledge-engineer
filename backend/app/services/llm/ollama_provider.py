import httpx

from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """
    Calls a locally-running Ollama instance. No API key, no network
    dependency beyond localhost - the ultimate free-tier fallback,
    and a good story for "what if all cloud LLM providers are down."
    """

    def __init__(self, model: str | None = None):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL

    def generate(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800) -> str:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=120.0,  # local inference can be slower than cloud APIs
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()