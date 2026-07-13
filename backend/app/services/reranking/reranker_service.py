import logging

from sentence_transformers import CrossEncoder

from app.core.config import settings

logger = logging.getLogger(__name__)


class RerankerService:
    """
    Wraps a cross-encoder model used to precisely re-score a small set
    of already-retrieved candidates. Loaded once as a singleton, same
    pattern as EmbeddingService - loading per-request would be far
    too slow.
    """

    def __init__(self):
        logger.info(f"Loading cross-encoder re-ranker: {settings.RERANKER_MODEL_NAME} ...")
        self.model = CrossEncoder(settings.RERANKER_MODEL_NAME)
        logger.info("Cross-encoder re-ranker loaded successfully.")

    def rerank(
        self, query: str, candidates: list[tuple[str, dict]]
    ) -> list[tuple[dict, float]]:
        """
        candidates: list of (point_id, payload) tuples from hybrid search.
        Returns candidates re-sorted by cross-encoder relevance score,
        best first, as (payload, score) tuples.
        """
        if not candidates:
            return []

        pairs = [(query, payload["content"]) for _, payload in candidates]
        scores = self.model.predict(pairs)

        scored = list(zip([payload for _, payload in candidates], scores))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored


reranker_service = RerankerService()