import os

#os.environ["HF_HUB_OFFLINE"] = "1"
#clearos.environ["TRANSFORMERS_OFFLINE"] = "1"

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.embedding.embedding_service import embedding_service  # noqa: F401
    from app.services.vectorstore.qdrant_service import qdrant_service  # noqa: F401
    from app.services.reranking.reranker_service import reranker_service  # noqa: F401
    logger.info("All startup models and services loaded.")

    yield

    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Enterprise AI knowledge platform with RAG and multi-agent orchestration.",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API is running"}