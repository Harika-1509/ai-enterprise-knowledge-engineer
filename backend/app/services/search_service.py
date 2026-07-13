import logging

from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from app.models.user import User
from app.schemas.search import SearchResult
from app.services.embedding.embedding_service import embedding_service
from app.services.search.fusion import reciprocal_rank_fusion
from app.services.vectorstore.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class SearchService:
    def search(self, query: str, limit: int, current_user: User) -> list[SearchResult]:
        access_filter = Filter(
            must=[FieldCondition(key="owner_id", match=MatchValue(value=str(current_user.id)))]
        )

        # Retrieve more candidates than requested from each path, so
        # fusion has enough material to work with before trimming to `limit`.
        candidate_limit = max(limit * 3, 15)

        # Dense (semantic) retrieval
        dense_vector = embedding_service.embed_query(query)
        dense_results = qdrant_service.search_dense(
            query_vector=dense_vector, limit=candidate_limit, query_filter=access_filter
        )

        # Sparse (keyword/BM25) retrieval
        from qdrant_client.http.models import SparseVector

        sparse_raw = embedding_service.embed_sparse_query(query)
        sparse_vector = SparseVector(
            indices=sparse_raw.indices.tolist(), values=sparse_raw.values.tolist()
        )
        sparse_results = qdrant_service.search_sparse(
            sparse_vector=sparse_vector, limit=candidate_limit, query_filter=access_filter
        )

        # Fuse both rankings by point ID
        dense_ids = [str(p.id) for p in dense_results]
        sparse_ids = [str(p.id) for p in sparse_results]
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids])

        # Build a lookup so we can recover full point data after fusion
        points_by_id = {str(p.id): p for p in dense_results + sparse_results}

        logger.info(
            f"Hybrid search by user {current_user.id}: query='{query}' "
            f"dense={len(dense_results)} sparse={len(sparse_results)} fused_top={len(fused)}"
        )

        results = []
        for point_id, fused_score in fused[:limit]:
            point = points_by_id[point_id]
            payload = point.payload
            results.append(
                SearchResult(
                    document_id=payload["document_id"],
                    filename=payload["filename"],
                    content=payload["content"],
                    score=fused_score,
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