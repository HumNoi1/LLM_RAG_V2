from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────
    app_env: str = "development"
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias=AliasChoices(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "ACCESS_TOKEN_EXPIRE_MINUTES"
        ),
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        validation_alias=AliasChoices(
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS", "REFRESH_TOKEN_EXPIRE_DAYS"
        ),
    )

    # ── Supabase ─────────────────────────────────────────────────
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_key: str = Field(default="", validation_alias="SUPABASE_KEY")
    supabase_service_role_key: str = Field(
        default="", validation_alias="SUPABASE_SERVICE_ROLE_KEY"
    )
    database_url: str = Field(default="", validation_alias="DATABASE_URL")

    # ── Groq API ─────────────────────────────────────────────────
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")

    # ── Qdrant ───────────────────────────────────────────────────
    qdrant_host: str = Field(default="localhost", validation_alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, validation_alias="QDRANT_PORT")
    qdrant_collection_name: str = Field(
        default="exam_documents", validation_alias="QDRANT_COLLECTION_NAME"
    )

    # ── Embedding ────────────────────────────────────────────────
    embedding_model: str = Field(
        default="BAAI/bge-m3", validation_alias="EMBEDDING_MODEL"
    )
    embedding_device: str = Field(default="cpu", validation_alias="EMBEDDING_DEVICE")
    embedding_batch_size: int = Field(
        default=32, validation_alias="EMBEDDING_BATCH_SIZE"
    )
    embedding_chunk_size: int = Field(
        default=512, validation_alias="EMBEDDING_CHUNK_SIZE"
    )
    embedding_chunk_overlap: int = Field(
        default=50, validation_alias="EMBEDDING_CHUNK_OVERLAP"
    )

    # ── Qdrant query params ──────────────────────────────────────
    qdrant_top_k: int = Field(default=5, validation_alias="QDRANT_TOP_K")
    qdrant_score_threshold: float = Field(
        default=0.3, validation_alias="QDRANT_SCORE_THRESHOLD"
    )

    # ── LLM ──────────────────────────────────────────────────────
    llm_model: str = Field(
        default="llama-3.3-70b-versatile", validation_alias="LLM_MODEL"
    )
    llm_temperature: float = Field(default=0.1, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, validation_alias="LLM_MAX_TOKENS")
    llm_request_timeout: int = Field(default=60, validation_alias="LLM_REQUEST_TIMEOUT")
    llm_max_retries: int = Field(default=3, validation_alias="LLM_MAX_RETRIES")
    llm_retry_base_delay: int = Field(
        default=2, validation_alias="LLM_RETRY_BASE_DELAY"
    )

    @property
    def secret_key(self) -> str:
        return self.jwt_secret_key

    @property
    def access_token_expire_minutes(self) -> int:
        return self.jwt_access_token_expire_minutes

    @property
    def refresh_token_expire_days(self) -> int:
        return self.jwt_refresh_token_expire_days

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — call get_settings() everywhere."""
    return Settings()
