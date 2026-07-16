from fastapi import APIRouter

from app.api.v1.endpoints import health, auth, admin, documents, search, ask, agent

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(ask.router, prefix="/ask", tags=["Ask"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])