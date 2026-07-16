import logging

from app.agents.state import AgentState
from app.services.generation.answer_service import answer_service
from app.repositories.user_repository import UserRepository
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


def rag_node(state: AgentState) -> AgentState:
    """
    Wraps the existing Phase 5/6 RAG pipeline (answer_service) as a
    graph node. This is deliberately a thin wrapper - all the real
    logic (retrieval, reranking, compression, generation, citations,
    confidence) already exists and is reused as-is, not reimplemented.
    """
    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_id(str(state["user_id"]))
        if not user:
            return {**state, "error": "User not found."}

        result = answer_service.ask(
            query=state["query"], limit=state.get("limit", 5), current_user=user
        )
        return {**state, "result": result}

    except Exception as e:
        logger.exception(f"rag_node failed: {e}")
        return {**state, "error": str(e)}
    finally:
        db.close()