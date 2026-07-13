import logging

from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from app.models.user import User
from app.schemas.search import SearchResult
from app.services.embedding.embedding_service import embedding_service
from app.services.vectorstore.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class SearchService:
    """
    Orchestrates the semantic search flow: embed query -> filtered
    vector search -> format results. Access control is enforced here,
    at the retrieval layer, not just at the API boundary.
    """

    def search(self, query: str, limit: int, current_user: User) -> list[SearchResult]:
        query_vector = embedding_service.embed_query(query)

        # Restrict search to documents owned by the current user.
        # (Later, RBAC could extend this to "owned OR shared with me",
        # but for now every user only sees their own knowledge base.)
        access_filter = Filter(
            must=[
                FieldCondition(
                    key="owner_id",
                    match=MatchValue(value=str(current_user.id)),
                )
            ]
        )

        raw_results = qdrant_service.search(
            query_vector=query_vector,
            limit=limit,
            query_filter=access_filter,
        )

        logger.info(
            f"Search by user {current_user.id}: query='{query}' "
            f"returned {len(raw_results)} results"
        )

        results = []
        for point in raw_results:
            payload = point.payload
            results.append(
                SearchResult(
                    document_id=payload["document_id"],
                    filename=payload["filename"],
                    content=payload["content"],
                    score=point.score,
                    chunk_index=payload["chunk_index"],
                    page_number=payload.get("page_number"),
                    slide_number=payload.get("slide_number"),
                    sheet_name=payload.get("sheet_name"),
                    paragraph_index=payload.get("paragraph_index"),
                    table_index=payload.get("table_index"),
                    row_index=payload.get("row_index"),
                )
            )
        return results

search_service = SearchService()