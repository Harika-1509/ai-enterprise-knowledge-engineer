from groq import Groq

from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    def __init__(self, model: str | None = None):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = model or settings.ANSWER_MODEL

    def generate(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip() 