import logging
import re

from app.schemas.answer import Citation
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)

# Matches [Source 1], [Source 1, 2], [Sources 1 and 2], [source 3] etc.
_CITATION_PATTERN = re.compile(r"\[Sources?\s+([\d,\s]+(?:and\s*\d+)?)\]", re.IGNORECASE)


def _describe_location(source: SearchResult) -> str | None:
    if source.page_number is not None:
        return f"page {source.page_number}"
    if source.slide_number is not None:
        return f"slide {source.slide_number}"
    if source.sheet_name is not None:
        return f"sheet '{source.sheet_name}'"
    if source.paragraph_index is not None:
        return f"paragraph {source.paragraph_index}"
    return None


def parse_citations(answer_text: str, sources: list[SearchResult]) -> list[Citation]:
    """
    Extracts [Source N] markers from the LLM's answer and maps each
    referenced number back to the SearchResult that occupied that
    position when the prompt was built (Step 22's build_context_block
    numbers sources in the exact same order as `sources` here).

    Deterministic parsing, not another LLM call - we already have all
    the metadata we need from retrieval; this is purely mechanical.
    """
    referenced_numbers: set[int] = set()

    for match in _CITATION_PATTERN.finditer(answer_text):
        raw_numbers = match.group(1)
        # Handles "1, 2", "1 and 2", "1,2" etc.
        cleaned = raw_numbers.replace("and", ",")
        for piece in cleaned.split(","):
            piece = piece.strip()
            if piece.isdigit():
                referenced_numbers.add(int(piece))

    citations = []
    for number in sorted(referenced_numbers):
        index = number - 1  # source numbers are 1-indexed in the prompt
        if index < 0 or index >= len(sources):
            logger.warning(
                f"Model cited [Source {number}] but only {len(sources)} "
                f"sources were provided - skipping invalid citation."
            )
            continue

        source = sources[index]
        citations.append(
            Citation(
                source_number=number,
                document_id=source.document_id,
                filename=source.filename,
                location=_describe_location(source),
                snippet=source.content,
            )
        )

    return citations