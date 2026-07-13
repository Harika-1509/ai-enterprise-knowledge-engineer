import logging

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Singleton service for interacting with Qdrant.
    Handles collection creation, vector upserts,
    semantic search, and document deletion.
    """

    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

        self.collection_name = settings.QDRANT_COLLECTION_NAME

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """
        Creates the collection only if it doesn't already exist.
        Safe to run every application startup.
        """
        collections = [
            c.name
            for c in self.client.get_collections().collections
        ]

        if self.collection_name in collections:
            logger.info(
                f"Qdrant collection '{self.collection_name}' already exists."
            )
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )

        logger.info(
            f"Created Qdrant collection '{self.collection_name}' "
            f"(dimension={settings.EMBEDDING_DIMENSION}, distance=Cosine)"
        )

    def upsert_points(self, points: list[PointStruct]) -> None:
        """
        Insert or update vector points.
        """
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        query_filter: Filter | None = None,
    ):
        """
        Semantic vector search.
        Compatible with qdrant-client >= 1.18.
        """

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )

        return response.points

    def delete_by_document_id(self, document_id: str) -> None:
        """
        Deletes every vector belonging to a document.
        """

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )


qdrant_service = QdrantService()