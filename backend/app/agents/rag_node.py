import logging

from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.generation.answer_service import answer_service

logger = logging.getLogger(__name__)


def rag_node(state: AgentState) -> AgentState:
    """
    Wraps the existing Phase 5/6 RAG pipeline. Content-level security
    scanning (Step 33) happens INSIDE answer_service.ask() itself now
    (see answer_service.py changes below) so every consumer of that
    method - direct QA, Planner's per-sub-question calls, Research's
    synthesis - automatically benefits from the same scanning, rather
    than each agent needing to remember to call the scanner separately.
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