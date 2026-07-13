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


qdrant_service = QdrantService()