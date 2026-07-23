from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings, loaded from environment variables.
    Using pydantic-settings gives us type validation and IDE autocomplete
    instead of scattering os.getenv() calls across the codebase.
    """

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    APP_NAME: str = "AI Enterprise Knowledge Engineer"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Cloud database (Neon)
    DATABASE_URL: str = ""

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = ""

    # ------------------------------------------------------------------
    # Qdrant
    # ------------------------------------------------------------------
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "documents"

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    STORAGE_DIR: str = "storage"
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: set[str] = {
        "pdf",
        "docx",
        "pptx",
        "xlsx",
        "txt",
    }

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_QUERY_INSTRUCTION: str = (
        "Represent this sentence for searching relevant passages: "
    )

    SPARSE_MODEL_NAME: str = "Qdrant/bm25"

    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_CANDIDATE_LIMIT: int = 15

    # ------------------------------------------------------------------
    # Groq
    # ------------------------------------------------------------------
    GROQ_API_KEY: str
    QUERY_REWRITER_MODEL: str = "llama-3.1-8b-instant"

    # ------------------------------------------------------------------
    # Context Compression
    # ------------------------------------------------------------------
    COMPRESSION_SIMILARITY_THRESHOLD: float = 0.55
    MAX_CONTEXT_TOKENS: int = 2000

    # ------------------------------------------------------------------
    # Answer Generation
    # ------------------------------------------------------------------
    ANSWER_MODEL: str = "llama-3.3-70b-versatile"
    ANSWER_TEMPERATURE: float = 0.1
    ANSWER_MAX_TOKENS: int = 800

    # ------------------------------------------------------------------
    # LLM Provider
    # ------------------------------------------------------------------
    DEFAULT_LLM_PROVIDER: str = "groq"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # Claude
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"

    # Fast/Quality Models
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"
    GROQ_QUALITY_MODEL: str = "llama-3.3-70b-versatile"

    GEMINI_FAST_MODEL: str = "gemini-1.5-flash"
    GEMINI_QUALITY_MODEL: str = "gemini-1.5-pro"

    OLLAMA_FAST_MODEL: str = "llama3.1:8b"
    OLLAMA_QUALITY_MODEL: str = "llama3.1:8b"

    ANTHROPIC_FAST_MODEL: str = "claude-3-5-haiku-latest"
    ANTHROPIC_QUALITY_MODEL: str = "claude-3-5-sonnet-latest"

    OPENAI_FAST_MODEL: str = "gpt-4o-mini"
    OPENAI_QUALITY_MODEL: str = "gpt-4o"

    # ------------------------------------------------------------------
    # n8n
    # ------------------------------------------------------------------
    N8N_WEBHOOK_BASE_URL: str = "http://localhost:5678"
    N8N_DOCUMENT_INGESTED_WEBHOOK_PATH: str = "/webhook/document-ingested"
    WEBHOOK_TIMEOUT_SECONDS: float = 5.0
    N8N_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    RESPONSE_VALIDATION_THRESHOLD: int = 3

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    #Oauth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
   # FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_URL: str  = "http://localhost:3001"

settings = Settings()