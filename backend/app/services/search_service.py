import logging

from qdrant_client.http.models import FieldCondition, Filter, MatchValue, SparseVector

from app.core.config import settings
from app.models.user import User
from app.schemas.search import SearchResult
from app.services.embedding.embedding_service import embedding_service
from app.services.query.query_rewriter_service import query_rewriter_service
from app.services.reranking.reranker_service import reranker_service
from app.services.search.fusion import reciprocal_rank_fusion
from app.services.vectorstore.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class SearchService:
    def search(self, query: str, limit: int, current_user: User) -> list[SearchResult]:
        # Stage 0: Query rewriting - improve the query BEFORE it hits retrieval
        search_query = query_rewriter_service.rewrite(query)

        access_filter = Filter(
            must=[FieldCondition(key="owner_id", match=MatchValue(value=str(current_user.id)))]
        )

        retrieval_limit = max(settings.RERANK_CANDIDATE_LIMIT, limit * 3)

        dense_vector = embedding_service.embed_query(search_query)
        dense_results = qdrant_service.search_dense(
            query_vector=dense_vector, limit=retrieval_limit, query_filter=access_filter
        )

        sparse_raw = embedding_service.embed_sparse_query(search_query)
        sparse_vector = SparseVector(
            indices=sparse_raw.indices.tolist(), values=sparse_raw.values.tolist()
        )
        sparse_results = qdrant_service.search_sparse(
            sparse_vector=sparse_vector, limit=retrieval_limit, query_filter=access_filter
        )

        dense_ids = [str(p.id) for p in dense_results]
        sparse_ids = [str(p.id) for p in sparse_results]
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids])

        points_by_id = {str(p.id): p for p in dense_results + sparse_results}

        candidate_ids = [point_id for point_id, _ in fused[: settings.RERANK_CANDIDATE_LIMIT]]
        candidates = [
            (point_id, points_by_id[point_id].payload) for point_id in candidate_ids
        ]

        logger.info(
            f"Hybrid retrieval by user {current_user.id}: original_query='{query}' "
            f"search_query='{search_query}' dense={len(dense_results)} "
            f"sparse={len(sparse_results)} candidates_for_rerank={len(candidates)}"
        )

        # Re-rank using the ORIGINAL query, not the rewritten one - the
        # cross-encoder should judge relevance against what the user
        # actually asked, while retrieval benefits from the clearer rewrite.
        reranked = reranker_service.rerank(query, candidates)

        logger.info(f"Re-ranked {len(reranked)} candidates for query='{query}'")

        results = []
        for payload, score in reranked[:limit]:
            results.append(
                SearchResult(
                    document_id=payload["document_id"],
                    filename=payload["filename"],
                    content=payload["content"],
                    score=float(score),
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
    

    def search_for_llm_context(self, query: str, limit: int, current_user: User) -> list[SearchResult]:
        """
        Same retrieval/rerank pipeline as search(), but additionally
        compresses chunk content for efficient LLM consumption. Used by
        the future RAG answer-generation endpoint (Phase 6), not the
        plain search endpoint - users browsing search results still see
        full, uncompressed chunk text for readability.
        """
        from app.services.compression.context_compressor import context_compressor

        results = self.search(query, limit, current_user)

        results_as_dicts = [r.model_dump() for r in results]
        compressed_dicts = context_compressor.compress_results(query, results_as_dicts)

        return [SearchResult(**d) for d in compressed_dicts]


search_service = SearchService()