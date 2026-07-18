import logging

from app.models.user import User
from app.schemas.search import SearchResult
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


class RetrieverAgent:
    """
    A generation-free retrieval capability: hybrid search + rerank +
    compression (Steps 17-21), with NO LLM answer generation on top.

    This exists as a reusable internal capability for other agents that
    need raw evidence/chunks without paying the cost of a full narrative
    answer - e.g. a future Research Agent gathering information across
    several searches before synthesizing once at the end, rather than
    generating (and discarding) a full answer per intermediate search.

    Deliberately NOT exposed as its own top-level API endpoint in this
    step - it's designed to be called directly by other graph nodes.
    A direct "/retrieve" endpoint could be added later if a genuine
    external use case emerges (e.g. a raw-search UI feature in Phase 9),
    but building it now without a concrete consumer would be speculative.
    """

    def retrieve(self, query: str, user: User, limit: int = 5) -> list[SearchResult]:
        results = search_service.search_for_llm_context(
            query=query, limit=limit, current_user=user
        )
        logger.info(
            f"RetrieverAgent: query='{query}' user={user.id} "
            f"returned {len(results)} compressed results (no generation)"
        )
        return results

    def retrieve_multi(
        self, queries: list[str], user: User, limit_per_query: int = 5
    ) -> dict[str, list[SearchResult]]:
        """
        Retrieves for multiple queries in one call, returning a dict
        keyed by query. Useful for a future agent (e.g. Research Agent,
        Step 31) that needs to gather evidence across several distinct
        angles on a topic before synthesizing - avoids each caller
        needing to hand-roll a loop over retrieve().
        """
        results = {}
        for query in queries:
            results[query] = self.retrieve(query, user, limit_per_query)
        return results


retriever_agent = RetrieverAgent()