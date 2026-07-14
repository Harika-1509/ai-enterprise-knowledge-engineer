import logging
import re

import numpy as np
import tiktoken

from app.core.config import settings
from app.services.embedding.embedding_service import embedding_service

logger = logging.getLogger(__name__)

_ENCODER = tiktoken.get_encoding("cl100k_base")

# Simple sentence boundary regex - splits on '.', '!', '?' followed by
# whitespace and a capital letter/quote, while avoiding common abbreviation
# false-positives (e.g. "Dr.", "e.g.") reasonably well for our use case.
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'])")


class ContextCompressor:
    """
    Compresses retrieved chunks by filtering out low-relevance sentences,
    then enforces an overall token budget across the combined context
    passed to the LLM. Reuses the existing embedding model rather than
    introducing a new dependency or LLM call per chunk.
    """

    def _split_sentences(self, text: str) -> list[str]:
        sentences = _SENTENCE_SPLIT_PATTERN.split(text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _token_count(self, text: str) -> int:
        return len(_ENCODER.encode(text))

    def compress_chunk(self, query: str, content: str) -> str:
        """
        Filters a single chunk's content down to only the sentences
        relevant to the query, preserving original sentence order.
        """
        sentences = self._split_sentences(content)

        # Very short chunks aren't worth splitting/filtering - the
        # overhead isn't justified and short text is usually already dense.
        if len(sentences) <= 2:
            return content

        query_vector = np.array(embedding_service.embed_query(query))
        sentence_vectors = np.array(embedding_service.embed_documents(sentences))

        similarities = sentence_vectors @ query_vector  # normalized vectors -> dot product = cosine

        kept_sentences = [
            sentence
            for sentence, sim in zip(sentences, similarities)
            if sim >= settings.COMPRESSION_SIMILARITY_THRESHOLD
        ]

        # Safety net: never compress a chunk down to nothing. If every
        # sentence fell below threshold, keep the single best one rather
        # than discarding the chunk's content entirely.
        if not kept_sentences:
            best_idx = int(np.argmax(similarities))
            kept_sentences = [sentences[best_idx]]

        return " ".join(kept_sentences)

    def compress_results(self, query: str, chunks: list[dict]) -> list[dict]:
        """
        chunks: list of dicts each containing at least a 'content' key
        (e.g., built from SearchResult.model_dump()).
        Returns the same structure with 'content' replaced by compressed
        text, trimmed further if needed to fit MAX_CONTEXT_TOKENS overall.
        """
        compressed = []
        total_tokens = 0

        for chunk in chunks:
            compressed_content = self.compress_chunk(query, chunk["content"])
            token_count = self._token_count(compressed_content)

            if total_tokens + token_count > settings.MAX_CONTEXT_TOKENS:
                remaining_budget = settings.MAX_CONTEXT_TOKENS - total_tokens
                if remaining_budget <= 0:
                    logger.info(
                        f"Context token budget ({settings.MAX_CONTEXT_TOKENS}) reached, "
                        f"dropping remaining {len(chunks) - len(compressed)} chunk(s)."
                    )
                    break
                tokens = _ENCODER.encode(compressed_content)[:remaining_budget]
                compressed_content = _ENCODER.decode(tokens)
                token_count = remaining_budget

            new_chunk = {**chunk, "content": compressed_content}
            compressed.append(new_chunk)
            total_tokens += token_count

        logger.info(
            f"Compressed {len(chunks)} chunks into {len(compressed)} chunks, "
            f"~{total_tokens} total tokens (budget={settings.MAX_CONTEXT_TOKENS})"
        )
        return compressed


context_compressor = ContextCompressor()