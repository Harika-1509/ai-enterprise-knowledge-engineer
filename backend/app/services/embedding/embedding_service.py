import logging

from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Wraps both a dense embedding model (semantic meaning) and a sparse
    BM25-style model (exact keyword matching). Both are needed for
    hybrid search - dense alone misses exact terms, sparse alone
    misses paraphrases/synonyms.
    """

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME} ...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded successfully.")

        logger.info(f"Loading sparse (BM25) model: {settings.SPARSE_MODEL_NAME} ...")
        self.sparse_model = SparseTextEmbedding(model_name=settings.SPARSE_MODEL_NAME)
        logger.info("Sparse model loaded successfully.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(
            texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        prefixed = settings.EMBEDDING_QUERY_INSTRUCTION + query
        embedding = self.model.encode(prefixed, normalize_embeddings=True)
        return embedding.tolist()

    def embed_sparse_documents(self, texts: list[str]):
        if not texts:
            return []
        return list(self.sparse_model.embed(texts))

    def embed_sparse_query(self, query: str):
        return list(self.sparse_model.embed([query]))[0]


embedding_service = EmbeddingService()