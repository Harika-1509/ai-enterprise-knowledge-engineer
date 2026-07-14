import google.generativeai as genai

from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, model: str | None = None):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = model or settings.GEMINI_MODEL

    def generate(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800) -> str:
        # Gemini's SDK doesn't use OpenAI-style role dicts natively - we
        # translate: system prompt gets prepended, roles get remapped.
        system_content = ""
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                gemini_role = "model" if msg["role"] == "assistant" else "user"
                conversation.append({"role": gemini_role, "parts": [msg["content"]]})

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_content or None,
        )
        response = model.generate_content(
            conversation,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text.strip()