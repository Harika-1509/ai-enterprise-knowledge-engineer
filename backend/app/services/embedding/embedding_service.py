import logging

from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Wraps a locally-run sentence-transformers model. Loaded once as a
    singleton (model loading takes a few seconds - we never want to
    reload it per-request).
    """

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME} ...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded successfully.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embeds a batch of chunk texts for storage. No instruction prefix -
        BGE models are trained asymmetrically: documents are embedded
        plain, only queries get the instruction prefix.
        """
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,  # required for cosine similarity in Qdrant
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Embeds a single user query for search. Applies BGE's recommended
        instruction prefix, which measurably improves retrieval quality
        for this model family.
        """
        prefixed = settings.EMBEDDING_QUERY_INSTRUCTION + query
        embedding = self.model.encode(
            prefixed,
            normalize_embeddings=True,
        )
        return embedding.tolist()


# Singleton - the model loads once when the app starts, not per-request.
embedding_service = EmbeddingService()