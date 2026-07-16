from app.schemas.answer import AskResponse
from app.schemas.search import SearchRequest
from pydantic import BaseModel


class AgentRequest(SearchRequest):
    pass


class AgentResponse(BaseModel):
    query: str
    intent: str
    result: AskResponse | None
    error: str | None