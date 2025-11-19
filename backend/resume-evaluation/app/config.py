from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:root@localhost/evaluv"
    ENVIRONMENT: str = "development"  # "development" or "production"
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_DECODE_RESPONSES: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds

    # Caching
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default cache TTL
    ENABLE_CACHING: bool = True

    # Qdrant Vector Database
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_PREFIX: str = "resume_eval"
    QDRANT_VECTOR_SIZE: int = 4096  # Updated for qwen/qwen3-embedding-8b
    QDRANT_DISTANCE_METRIC: str = "Cosine"
    QDRANT_ENABLE_HNSW: bool = True

    # Embeddings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENROUTER_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "qwen/qwen3-embedding-8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "qwen3-embedding:0.6b"

    EMBEDDING_MAX_TOKENS: int = 8191  # Maximum tokens for embeddings

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
