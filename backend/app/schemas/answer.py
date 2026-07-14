from app.schemas.search import SearchRequest, SearchResult
from pydantic import BaseModel


class AskRequest(SearchRequest):
    pass


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: list[SearchResult]