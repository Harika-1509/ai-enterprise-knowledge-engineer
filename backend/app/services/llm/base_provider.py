from abc import ABC, abstractmethod
from typing import Iterator


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_stream(
        self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 800
    ) -> Iterator[str]:
        """
        Yields text chunks (token fragments) as they're generated.
        Every provider must support this - it's part of the core
        contract now, not an optional extra.
        """
        raise NotImplementedError