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


class LLMProviderFactory:
    """
    Factory Pattern (same as Step 8's ExtractorFactory): hides provider
    instantiation details from callers, who just ask for "the configured
    provider" or a specific named one, without knowing which SDK or
    credentials are involved.
    """

    @classmethod
    def get_provider(cls, provider_name: str | None = None, model: str | None = None) -> BaseLLMProvider:
        name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
        provider_class = _PROVIDER_REGISTRY.get(name)
        if provider_class is None:
            raise ValueError(
                f"Unknown LLM provider '{name}'. Available: {list(_PROVIDER_REGISTRY.keys())}"
            )
        return provider_class(model=model)