import logging

import numpy as np
import pysbd
import tiktoken

from app.core.config import settings
from app.services.embedding.embedding_service import embedding_service

logger = logging.getLogger(__name__)

_ENCODER = tiktoken.get_encoding("cl100k_base")
_SEGMENTER = pysbd.Segmenter(language="en", clean=False)


class ContextCompressor:
    def _split_sentences(self, text: str) -> list[str]:
        raw_sentences = _SEGMENTER.segment(text.strip())
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        # Discard citation/reference fragments and other junk: very short
        # "sentences" (single words, page numbers, journal abbreviations
        # like "Int." or "Sci.") aren't real content and shouldn't be
        # scored or kept - they add noise without adding information.
        return [s for s in sentences if len(s) >= 25 and len(s.split()) >= 4]

    def _token_count(self, text: str) -> int:
        return len(_ENCODER.encode(text))

    def compress_chunk(self, query: str, content: str) -> str:
        sentences = self._split_sentences(content)
        if len(sentences) <= 2:
            return content

        query_vector = np.array(embedding_service.embed_query(query))
        sentence_vectors = np.array(embedding_service.embed_documents(sentences))
        similarities = sentence_vectors @ query_vector

        kept_sentences = [
            sentence for sentence, sim in zip(sentences, similarities)
            if sim >= settings.COMPRESSION_SIMILARITY_THRESHOLD
        ]

        if not kept_sentences:
            best_idx = int(np.argmax(similarities))
            kept_sentences = [sentences[best_idx]]

        result = " ".join(kept_sentences)
        return result if len(result) <= len(content) else content

    def compress_results(self, query: str, chunks: list[dict]) -> list[dict]:
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