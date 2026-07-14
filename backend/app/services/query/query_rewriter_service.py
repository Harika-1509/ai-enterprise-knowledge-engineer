import logging

from app.core.config import settings
from app.services.llm.llm_factory import LLMProviderFactory

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a query rewriting assistant for a semantic search system.

Your ONLY job is to rewrite the user's query to be clearer and more effective \
for search retrieval. You must NEVER change the user's underlying intent, add \
assumptions, or answer the question yourself.

Rules:
- If the query is already clear and well-formed, return it unchanged.
- Resolve vague references only if context makes them obvious; otherwise leave as-is.
- Expand acronyms or add closely related terms ONLY if it clearly helps retrieval.
- Never add information not implied by the original query.
- Output ONLY the rewritten query text. No explanation, no quotes, no preamble.
"""


class QueryRewriterService:
    def __init__(self):
        # Uses a small, fast model regardless of provider - query rewriting
        # is a lightweight mechanical task, not one requiring a large model.
        self.provider = LLMProviderFactory.get_provider(model=settings.QUERY_REWRITER_MODEL)

    def rewrite(self, query: str) -> str:
        query = query.strip()
        if not query:
            return query

        try:
            rewritten = self.provider.generate(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
                max_tokens=150,
            )

            if self._is_safe_rewrite(query, rewritten):
                logger.info(f"Query rewritten: '{query}' -> '{rewritten}'")
                return rewritten

            logger.warning(f"Rewrite for '{query}' failed safety check, falling back to original.")
            return query

        except Exception as e:
            logger.exception(f"Query rewriting failed, falling back to original query: {e}")
            return query

    def _is_safe_rewrite(self, original: str, rewritten: str) -> bool:
        if not rewritten:
            return False
        if len(rewritten) > len(original) * 4 + 50:
            return False
        return True


query_rewriter_service = QueryRewriterService()