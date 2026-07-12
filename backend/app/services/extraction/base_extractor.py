from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExtractedChunk:
    """
    One unit of extracted content with source metadata.
    We keep metadata (page/slide/sheet number) at extraction time,
    because it's needed later for citations - it's much harder to
    recover this information after the text has been flattened.
    """
    content: str
    metadata: dict = field(default_factory=dict)


class BaseExtractor(ABC):
    """
    Strategy interface. Every file-type extractor implements this,
    so the rest of the app never needs to know which library is
    actually parsing a given file.
    """

    @abstractmethod
    def extract(self, file_path: Path) -> list[ExtractedChunk]:
        """Returns a list of extracted text segments with metadata."""
        raise NotImplementedError