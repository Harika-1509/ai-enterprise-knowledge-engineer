import logging

from sentence_transformers import CrossEncoder

from app.core.config import settings

logger = logging.getLogger(__name__)


class RerankerService:
    """
    Wraps a cross-encoder model used to precisely re-score a small set
    of already-retrieved candidates.

    The model is loaded lazily on first use instead of application startup.
    """

    def __init__(self):
        self.model = None

    def _ensure_loaded(self):
        """
        Load the CrossEncoder model only when it is first needed.
        """
        if self.model is None:
            logger.info(
                f"Loading cross-encoder re-ranker: {settings.RERANKER_MODEL_NAME} ..."
            )
            self.model = CrossEncoder(settings.RERANKER_MODEL_NAME)
            logger.info("Cross-encoder re-ranker loaded successfully.")

    def rerank(
        self,
        query: str,
        candidates: list[tuple[str, dict]],
    ) -> list[tuple[dict, float]]:
        """
        candidates: list of (point_id, payload) tuples from hybrid search.

        Returns:
            list[(payload, score)] sorted by descending relevance score.
        """
        if not candidates:
            return []

        # Load the model only when reranking is actually requested
        self._ensure_loaded()

        pairs = [(query, payload["content"]) for _, payload in candidates]

        scores = self.model.predict(pairs)

        scored = list(zip([payload for _, payload in candidates], scores))
        scored.sort(key=lambda item: item[1], reverse=True)

        return scored


reranker_service = RerankerService()