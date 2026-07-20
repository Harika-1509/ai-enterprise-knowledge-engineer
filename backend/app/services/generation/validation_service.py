import logging

from app.core.config import settings
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Runtime validation gate: reuses Step 42's faithfulness scoring
    (same LLM-as-judge technique, fast model tier) but applied to
    every live answer, not just an offline dataset. Deliberately
    lightweight - a single fast-tier LLM call, not the full 3-metric
    evaluation suite from Step 42, since this runs on every request.
    """

    def validate(self, answer: str, sources: list[SearchResult]) -> str | None:
        if not sources or not answer.strip():
            return None  # nothing to validate against - refusals are trivially "faithful"

        from evaluation.metrics import score_faithfulness  # reused, not duplicated

        sources_text = "\n\n".join(s.content for s in sources)

        try:
            score = score_faithfulness(answer, sources_text)
        except Exception as e:
            logger.warning(f"Runtime validation failed to run, skipping: {e}")
            return None  # validation itself failing must never block the response

        if 0 < score < settings.RESPONSE_VALIDATION_THRESHOLD:
            logger.warning(f"Response validation flagged low faithfulness (score={score}) for answer: {answer[:100]}")
            return (
                "This answer may not be fully supported by the source documents. "
                "Please verify against the cited sources."
            )
        return None


validation_service = ValidationService()