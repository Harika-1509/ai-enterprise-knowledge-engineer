import logging

from app.core.config import settings
from app.schemas.answer import Citation, Confidence, ConfidenceLevel
from app.schemas.search import SearchResult
from app.services.llm.llm_factory import LLMProviderFactory

logger = logging.getLogger(__name__)

_VERIFICATION_SYSTEM_PROMPT = """You are a strict fact-checking assistant. You will be \
given a set of source excerpts and an answer that claims to be based on them.

Determine whether the answer is FULLY supported by the sources - every claim in the \
answer must be traceable to the provided sources, with no unsupported additions.

Respond with EXACTLY one word: "yes" if fully supported, "partial" if mostly but not \
entirely supported, or "no" if significantly unsupported or contradicted. No explanation."""


class ConfidenceService:
    def __init__(self):
        # Self-verification is a narrow, cheap classification task -
        # use the fast/small model tier, same reasoning as query rewriting.
        self.provider = LLMProviderFactory.get_provider(task="fast")

    def _retrieval_score(self, citations: list[Citation], sources: list[SearchResult]) -> float:
        """
        Averages the re-rank relevance of only the sources actually
        cited in the answer - not all retrieved sources, since some
        may have been correctly ignored by the model.
        """
        if not citations:
            return 0.0

        cited_numbers = {c.source_number for c in citations}
        cited_scores = [
            sources[n - 1].score for n in cited_numbers if 0 < n <= len(sources)
        ]
        if not cited_scores:
            return 0.0

        # Cross-encoder scores aren't bounded 0-1 (Step 19) - normalize
        # with a sigmoid-like squashing so this combines sensibly with
        # the 0-1 self-verification signal below.
        import math
        avg_raw = sum(cited_scores) / len(cited_scores)
        return 1 / (1 + math.exp(-avg_raw))  # logistic squashing to (0,1)

    def _self_verify(self, answer: str, sources: list[SearchResult]) -> bool | None:
        if not sources or not answer.strip():
            return None

        context = "\n\n".join(f"[Source {i+1}] {s.content}" for i, s in enumerate(sources))
        prompt = f"SOURCES:\n{context}\n\nANSWER TO VERIFY:\n{answer}"

        try:
            result = self.provider.generate(
                messages=[
                    {"role": "system", "content": _VERIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=10,
            )
            verdict = result.strip().lower()
            if "yes" in verdict:
                return True
            if "no" in verdict:
                return False
            return None  # "partial" or unparseable -> treat as inconclusive, not a hard fail
        except Exception as e:
            logger.warning(f"Self-verification call failed, skipping: {e}")
            return None

    def assess(
        self, answer: str, sources: list[SearchResult], citations: list[Citation]
    ) -> Confidence:
        retrieval_score = self._retrieval_score(citations, sources)
        self_verified = self._self_verify(answer, sources)

        # Combine signals into a level. Deliberately simple, transparent
        # rules rather than a black-box weighted formula - easy to
        # explain and to recalibrate later based on Phase 10 evaluation.
        if not citations:
            level = ConfidenceLevel.LOW
            reasoning = "No sources were cited in the answer."
        elif self_verified is False:
            level = ConfidenceLevel.LOW
            reasoning = "Self-verification indicates the answer may not be fully supported by sources."
        elif retrieval_score >= 0.65 and self_verified is True:
            level = ConfidenceLevel.HIGH
            reasoning = "Strong source relevance and the answer was verified as well-supported."
        elif retrieval_score >= 0.5 or self_verified is True:
            level = ConfidenceLevel.MEDIUM
            reasoning = "Reasonable source relevance, but not strongly confirmed on all signals."
        else:
            level = ConfidenceLevel.LOW
            reasoning = "Weak source relevance and verification could not confirm the answer."

        return Confidence(
            level=level,
            retrieval_score=round(retrieval_score, 3),
            self_verified=self_verified,
            reasoning=reasoning,
        )


confidence_service = ConfidenceService()