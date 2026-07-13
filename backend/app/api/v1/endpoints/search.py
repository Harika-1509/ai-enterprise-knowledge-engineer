from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import search_service

router = APIRouter()


@router.post("/", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    results = search_service.search(
        query=request.query, limit=request.limit, current_user=current_user
    )
    return SearchResponse(query=request.query, results=results)