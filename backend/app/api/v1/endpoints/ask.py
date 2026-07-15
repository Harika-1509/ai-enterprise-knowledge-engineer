from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.answer import AskRequest, AskResponse
from app.services.generation.answer_service import answer_service

router = APIRouter()


@router.post("/", response_model=AskResponse)
def ask_question(request: AskRequest, current_user: User = Depends(get_current_user)):
    return answer_service.ask(query=request.query, limit=request.limit, current_user=current_user)


@router.post("/stream")
def ask_question_stream(request: AskRequest, current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        answer_service.ask_stream(query=request.query, limit=request.limit, current_user=current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disables proxy buffering (relevant if deployed behind nginx later)
        },
    )