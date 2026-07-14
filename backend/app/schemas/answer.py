import uuid

from pydantic import BaseModel

from app.schemas.search import SearchRequest, SearchResult


class AskRequest(SearchRequest):
    pass


class Citation(BaseModel):
    source_number: int
    document_id: uuid.UUID
    filename: str
    location: str | None = None  # e.g. "page 4", "slide 2", "paragraph 7"
    snippet: str  # the actual chunk content backing this citation


class AskResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    sources: list[SearchResult]