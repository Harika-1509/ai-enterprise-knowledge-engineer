from fastapi import APIRouter, Depends

from app.agents.graph import agent_graph
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.agent import AgentRequest, AgentResponse

router = APIRouter()


@router.post("/", response_model=AgentResponse)
def run_agent(request: AgentRequest, current_user: User = Depends(get_current_user)):
    initial_state = {
        "query": request.query,
        "user_id": current_user.id,
        "limit": request.limit,
    }

    final_state = agent_graph.invoke(initial_state)

    return AgentResponse(
        query=request.query,
        intent=final_state.get("intent", "unknown"),
        result=final_state.get("result"),
        error=final_state.get("error"),
    )