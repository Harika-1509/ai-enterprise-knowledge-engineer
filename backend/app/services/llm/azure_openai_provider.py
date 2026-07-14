from openai import AzureOpenAI

from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider


class AzureOpenAIProvider(BaseLLMProvider):
    def __init__(self, model: str | None = None):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        self.deployment = model or settings.AZURE_OPENAI_DEPLOYMENT

    def generate(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()