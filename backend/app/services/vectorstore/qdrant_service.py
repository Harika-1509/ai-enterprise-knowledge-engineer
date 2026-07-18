import logging

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing_collections = [c.name for c in self.client.get_collections().collections]

        if self.collection_name in existing_collections:
            logger.info(f"Qdrant collection '{self.collection_name}' already exists.")
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                DENSE_VECTOR_NAME: VectorParams(
                    size=settings.EMBEDDING_DIMENSION, distance=Distance.COSINE
                )
            },
            sparse_vectors_config={SPARSE_VECTOR_NAME: SparseVectorParams()},
        )
        logger.info(
            f"Created Qdrant collection '{self.collection_name}' with named "
            f"dense ('{DENSE_VECTOR_NAME}') and sparse ('{SPARSE_VECTOR_NAME}') vectors."
        )

    def upsert_points(self, points: list[PointStruct]) -> None:
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search_dense(self, query_vector: list[float], limit: int = 10, query_filter: Filter | None = None):
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using=DENSE_VECTOR_NAME,
            limit=limit,
            query_filter=query_filter,
        )
        return response.points

    def search_sparse(self, sparse_vector: SparseVector, limit: int = 10, query_filter: Filter | None = None):
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=sparse_vector,
            using=SPARSE_VECTOR_NAME,
            limit=limit,
            query_filter=query_filter,
        )
        return response.points

    def delete_by_document_id(self, document_id: str) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )
    
    def get_all_chunks_for_document(self, document_id: str) -> list[dict]:
        """
        Retrieves EVERY chunk belonging to one document, ordered by
        chunk_index. This is a filter+scroll operation, NOT a similarity
        search - there's no query to rank against, since the goal is
        "give me the whole document," not "give me the most relevant parts."
        """
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
            limit=1000,  # generous ceiling - a single document is very
            # unlikely to exceed 1000 chunks; if it did, this would need
            # proper pagination, flagged honestly as a scale limit
        )
        payloads = [p.payload for p in points]
        payloads.sort(key=lambda p: p.get("chunk_index", 0))
        return payloads


qdrant_service = QdrantService()