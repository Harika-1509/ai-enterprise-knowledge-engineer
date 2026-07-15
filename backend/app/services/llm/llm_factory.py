from app.core.config import settings
from app.services.llm.azure_openai_provider import AzureOpenAIProvider
from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider

_PROVIDER_REGISTRY: dict[str, type[BaseLLMProvider]] = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "azure_openai": AzureOpenAIProvider,
}

# Maps (provider_name, task) -> the correct model name for THAT provider.
# This is what prevents a Groq model name from ever being sent to Gemini.
_TASK_MODEL_MAP: dict[str, dict[str, str]] = {
    "groq": {"fast": settings.GROQ_FAST_MODEL, "quality": settings.GROQ_QUALITY_MODEL},
    "gemini": {"fast": settings.GEMINI_FAST_MODEL, "quality": settings.GEMINI_QUALITY_MODEL},
    "ollama": {"fast": settings.OLLAMA_FAST_MODEL, "quality": settings.OLLAMA_QUALITY_MODEL},
    "claude": {"fast": settings.ANTHROPIC_FAST_MODEL, "quality": settings.ANTHROPIC_QUALITY_MODEL},
    "openai": {"fast": settings.OPENAI_FAST_MODEL, "quality": settings.OPENAI_QUALITY_MODEL},
    "azure_openai": {"fast": settings.AZURE_OPENAI_DEPLOYMENT, "quality": settings.AZURE_OPENAI_DEPLOYMENT},
}


class LLMProviderFactory:
    @classmethod
    def get_provider(
        cls, provider_name: str | None = None, task: str = "quality"
    ) -> BaseLLMProvider:
        """
        task: "fast" (lightweight, e.g. query rewriting) or "quality"
        (answer generation). The factory resolves this to the CORRECT
        model name for whichever provider is configured - callers never
        need to know or specify a provider-specific model name.
        """
        name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
        provider_class = _PROVIDER_REGISTRY.get(name)
        if provider_class is None:
            raise ValueError(
                f"Unknown LLM provider '{name}'. Available: {list(_PROVIDER_REGISTRY.keys())}"
            )

        model = _TASK_MODEL_MAP.get(name, {}).get(task)
        return provider_class(model=model)