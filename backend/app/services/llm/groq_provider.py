from typing import Iterator

from groq import Groq

from app.services.llm.base_provider import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    def __init__(self, model: str | None = None):
        from app.core.config import settings
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = model

    def generate(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def generate_stream(
        self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800
    ) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta