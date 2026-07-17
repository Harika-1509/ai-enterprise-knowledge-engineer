from typing import TypedDict
from uuid import UUID

from app.schemas.answer import AskResponse
from app.schemas.search import SearchResult


class AgentState(TypedDict, total=False):
    query: str
    user_id: UUID
    limit: int

    intent: str
    intent_reasoning: str

    # Planner (Step 29)
    sub_questions: list[str]
    sub_answers: list[AskResponse]

    # Research (this step)
    research_angles: list[str]
    research_evidence: list[SearchResult]

    result: AskResponse | None
    error: str | None