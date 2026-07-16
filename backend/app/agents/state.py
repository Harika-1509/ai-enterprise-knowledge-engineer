from typing import TypedDict
from uuid import UUID

from app.schemas.answer import AskResponse


class AgentState(TypedDict, total=False):
    """
    Shared state passed between every graph node. Extended in this step
    to carry sub-question/sub-answer data through the planner's internal
    stages, while remaining fully backward-compatible with rag_node's
    simpler usage from Step 28 (total=False means these new fields are
    just absent, not erroring, for non-planner paths).
    """
    query: str
    user_id: UUID
    limit: int

    intent: str
    intent_reasoning: str

    sub_questions: list[str]
    sub_answers: list[AskResponse]

    result: AskResponse | None
    error: str | None