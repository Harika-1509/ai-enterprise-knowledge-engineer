from typing import TypedDict
from uuid import UUID

from app.schemas.answer import AskResponse


class AgentState(TypedDict, total=False):
    """
    Shared state passed between every node in the graph. Each node
    reads what it needs and writes updates back - LangGraph merges
    these updates automatically between node calls.
    """
    query: str
    user_id: UUID
    limit: int

    intent: str  # set by supervisor_node
    intent_reasoning: str

    result: AskResponse | None  # set by whichever downstream node handles the request
    error: str | None