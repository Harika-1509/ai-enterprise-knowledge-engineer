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

settings = Settings()