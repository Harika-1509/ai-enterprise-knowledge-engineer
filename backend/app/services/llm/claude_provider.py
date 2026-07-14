from anthropic import Anthropic

from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    def __init__(self, model: str | None = None):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = model or settings.ANTHROPIC_MODEL

    def generate(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800) -> str:
        # Anthropic's API takes system prompt as a separate top-level
        # parameter, not as a message in the list - another example of
        # per-provider translation the abstraction hides from callers.
        system_content = ""
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                conversation.append(msg)

        response = self.client.messages.create(
            model=self.model,
            system=system_content,
            messages=conversation,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text.strip()