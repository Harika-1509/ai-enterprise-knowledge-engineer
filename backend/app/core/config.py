from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings, loaded from environment variables.
    Using pydantic-settings gives us type validation and IDE autocomplete
    instead of scattering os.getenv() calls across the codebase.
    """

    # App
    APP_NAME: str = "AI Enterprise Knowledge Engineer"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Storage
    STORAGE_DIR: str = "storage"
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: set[str] = {"pdf", "docx", "pptx", "xlsx", "txt"}

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_QUERY_INSTRUCTION: str = "Represent this sentence for searching relevant passages: "

    QDRANT_COLLECTION_NAME: str = "documents"

    SPARSE_MODEL_NAME: str = "Qdrant/bm25"

    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_CANDIDATE_LIMIT: int = 15

    # Groq (used temporarily for query rewriting until Phase 6's
    # multi-LLM abstraction is built)
    GROQ_API_KEY: str
    QUERY_REWRITER_MODEL: str = "llama-3.1-8b-instant"

    # Context Compression
    COMPRESSION_SIMILARITY_THRESHOLD: float = 0.55
    MAX_CONTEXT_TOKENS: int = 2000

    # Answer Generation (temporary direct Groq usage, formalized in Phase 6)
    ANSWER_MODEL: str = "llama-3.3-70b-versatile"
    ANSWER_TEMPERATURE: float = 0.1
    ANSWER_MAX_TOKENS: int = 800

   # LLM Provider Selection (config-driven, no code changes needed to switch)
    DEFAULT_LLM_PROVIDER: str = "ollama"  # groq | gemini | ollama | claude | openai | azure_openai

    # Provider credentials / settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"

   # Task-oriented model selection: which model each provider should use
    # for "fast/cheap" tasks (query rewriting) vs "quality" tasks (answer
    # generation). Avoids ever passing one provider's model name to another.
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"
    GROQ_QUALITY_MODEL: str = "llama-3.3-70b-versatile"

    GEMINI_FAST_MODEL: str = "gemini-1.5-flash"
    GEMINI_QUALITY_MODEL: str = "gemini-1.5-pro"

    OLLAMA_FAST_MODEL: str = "llama3.1:8b"
    OLLAMA_QUALITY_MODEL: str = "llama3.1:8b"  # same model, Ollama has no separate "fast" tier locally

    ANTHROPIC_FAST_MODEL: str = "claude-3-5-haiku-latest"
    ANTHROPIC_QUALITY_MODEL: str = "claude-3-5-sonnet-latest"

    OPENAI_FAST_MODEL: str = "gpt-4o-mini"
    OPENAI_QUALITY_MODEL: str = "gpt-4o"
settings = Settings()