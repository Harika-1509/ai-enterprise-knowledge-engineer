from fastapi import FastAPI
from fastapi.security import HTTPBearer

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Enterprise AI knowledge platform with RAG and multi-agent orchestration.",
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API is running"}