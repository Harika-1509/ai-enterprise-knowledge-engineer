import uuid
from enum import Enum

from pydantic import BaseModel

from app.schemas.search import SearchRequest, SearchResult


class AskRequest(SearchRequest):
    pass


class Citation(BaseModel):
    source_number: int
    document_id: uuid.UUID
    filename: str
    location: str | None = None
    snippet: str


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Confidence(BaseModel):
    level: ConfidenceLevel
    retrieval_score: float  # 0-1, avg re-rank relevance of cited sources
    self_verified: bool | None  # None if verification call failed/skipped
    reasoning: str


class AskResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    sources: list[SearchResult]
    confidence: Confidence
    validation_warning: str | None = None