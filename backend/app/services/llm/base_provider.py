from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """
    Strategy interface every LLM provider implements. Deliberately
    minimal - the common denominator across chat-completion APIs:
    a list of role-tagged messages in, generated text out.
    """

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 800,
    ) -> str:
        """
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        Returns the generated text content.
        """
        raise NotImplementedError