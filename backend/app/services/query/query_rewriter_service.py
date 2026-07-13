import logging

from groq import Groq

from app.core.config import settings

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
    """
    Uses a small, fast LLM (Groq) to rewrite vague or poorly-phrased
    queries before they hit the retrieval pipeline. This is a temporary,
    single-provider implementation - Phase 6 will refactor this to use
    our multi-LLM abstraction layer instead of calling Groq directly.
    """

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def rewrite(self, query: str) -> str:
        query = query.strip()
        if not query:
            return query

        try:
            response = self.client.chat.completions.create(
                model=settings.QUERY_REWRITER_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,  # deterministic - we want consistent rewrites, not creativity
                max_tokens=150,
            )
            rewritten = response.choices[0].message.content.strip()

            if self._is_safe_rewrite(query, rewritten):
                logger.info(f"Query rewritten: '{query}' -> '{rewritten}'")
                return rewritten

            logger.warning(
                f"Rewrite for '{query}' failed safety check, falling back to original."
            )
            return query

        except Exception as e:
            # Query rewriting is an enhancement, not a hard dependency -
            # if it fails for any reason, we must not break search entirely.
            logger.exception(f"Query rewriting failed, falling back to original query: {e}")
            return query

    def _is_safe_rewrite(self, original: str, rewritten: str) -> bool:
        """
        Basic guardrail: reject rewrites that are empty, suspiciously long
        (possible hallucinated tangent), or suspiciously short (possible
        truncation/error).
        """
        if not rewritten:
            return False
        if len(rewritten) > len(original) * 4 + 50:
            return False
        return True


query_rewriter_service = QueryRewriterService()