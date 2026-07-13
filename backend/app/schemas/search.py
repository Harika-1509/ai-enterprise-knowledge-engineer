import uuid

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    document_id: uuid.UUID
    filename: str
    content: str
    score: float
    chunk_index: int
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    paragraph_index: int | None = None
    table_index: int | None = None
    row_index: int | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]