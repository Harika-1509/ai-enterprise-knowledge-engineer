import re
from dataclasses import dataclass, field

import tiktoken

from app.services.extraction.base_extractor import ExtractedChunk

# cl100k_base is the tokenizer used by GPT-3.5/4 and is a reasonable,
# widely-used approximation for token counting even when we later use
# non-OpenAI embedding models - it's a consistent yardstick, not a
# requirement that we use an OpenAI model.
_ENCODER = tiktoken.get_encoding("cl100k_base")


@dataclass
class TextChunk:
    """A final, embedding-ready chunk with full lineage metadata."""

    content: str
    chunk_index: int
    token_count: int
    metadata: dict = field(default_factory=dict)


class TextChunker:
    """
    Recursive text splitter: tries to split on the largest natural
    boundary first (paragraphs), and only falls back to smaller
    boundaries (sentences, then words) if a piece is still too large.
    This keeps chunks as semantically coherent as possible while
    still respecting a hard token budget.
    """

    def __init__(self, max_tokens: int = 500, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        # Ordered from largest natural boundary to smallest fallback
        self._separators = ["\n\n", "\n", ". ", " "]

    def _token_count(self, text: str) -> int:
        return len(_ENCODER.encode(text))

    def _split_on_separator(self, text: str, separator: str) -> list[str]:
        if separator == " ":
            return text.split(" ")
        # Keep the separator attached so we don't lose sentence punctuation
        parts = re.split(f"({re.escape(separator)})", text)
        merged = []
        for i in range(0, len(parts) - 1, 2):
            merged.append(parts[i] + parts[i + 1])
        if len(parts) % 2 == 1 and parts[-1]:
            merged.append(parts[-1])
        return merged if merged else [text]

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        if self._token_count(text) <= self.max_tokens:
            return [text]

        if not separators:
            # Last resort: hard-cut by token slice, no natural boundary left
            tokens = _ENCODER.encode(text)
            return [
                _ENCODER.decode(tokens[i : i + self.max_tokens])
                for i in range(0, len(tokens), self.max_tokens)
            ]

        separator, remaining_separators = separators[0], separators[1:]
        pieces = self._split_on_separator(text, separator)

        results = []
        buffer = ""
        for piece in pieces:
            candidate = buffer + piece
            if self._token_count(candidate) <= self.max_tokens:
                buffer = candidate
            else:
                if buffer:
                    results.append(buffer)
                if self._token_count(piece) > self.max_tokens:
                    # This single piece is still too big - recurse with a smaller separator
                    results.extend(self._recursive_split(piece, remaining_separators))
                    buffer = ""
                else:
                    buffer = piece
        if buffer:
            results.append(buffer)
        return results

    def _add_overlap(self, pieces: list[str]) -> list[str]:
        """
        Prepends the tail of the previous chunk to each chunk (except the
        first), so context isn't abruptly lost at chunk boundaries.
        """
        if self.overlap_tokens <= 0 or len(pieces) <= 1:
            return pieces

        overlapped = [pieces[0]]
        for i in range(1, len(pieces)):
            prev_tokens = _ENCODER.encode(pieces[i - 1])
            overlap_slice = prev_tokens[-self.overlap_tokens :]
            overlap_text = _ENCODER.decode(overlap_slice)
            overlapped.append(overlap_text + pieces[i])
        return overlapped

    def split(self, extracted_chunk: ExtractedChunk) -> list[TextChunk]:
        """
        Splits one ExtractedChunk (e.g. one PDF page) into one or more
        TextChunks, each carrying forward the original metadata plus
        its own chunk_index and token_count.
        """
        raw_pieces = self._recursive_split(extracted_chunk.content, self._separators)
        pieces_with_overlap = self._add_overlap(raw_pieces)

        chunks = []
        for idx, piece in enumerate(pieces_with_overlap):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append(
                TextChunk(
                    content=piece,
                    chunk_index=idx,
                    token_count=self._token_count(piece),
                    metadata={**extracted_chunk.metadata},
                )
            )
        return chunks


text_chunker = TextChunker()