# Configuration management for QURAN AI API service

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Any, Literal, Optional
import os
from urllib.parse import urlsplit

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # App settings
    app_name: str = "QURAN AI API"
    version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Server settings
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    workers: int = Field(default=1, validation_alias="WORKERS")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        validation_alias="CORS_ORIGINS",
    )

    # Database
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, validation_alias="DATABASE_POOL_SIZE")
    database_timeout: int = Field(default=30, validation_alias="DATABASE_TIMEOUT")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    redis_pool_size: int = Field(default=10, validation_alias="REDIS_POOL_SIZE")
    redis_timeout: int = Field(default=5, validation_alias="REDIS_TIMEOUT")

    # Quran Foundation API
    quran_api_base_url: str = Field(default="https://apis.quran.foundation", validation_alias="QURAN_API_BASE_URL")
    quran_api_client_id: str = Field(default="REPLACE_WITH_APPROVED_CLIENT_ID", validation_alias="QURAN_API_CLIENT_ID")
    quran_api_client_secret: str = Field(default="REPLACE_WITH_SECRET", validation_alias="QURAN_API_CLIENT_SECRET")
    quran_api_token_cache_ttl: int = Field(default=3300, validation_alias="QURAN_API_TOKEN_CACHE_TTL_SECONDS")
    quran_api_auth_base_url: Optional[str] = Field(default=None, validation_alias="QURAN_API_AUTH_BASE_URL")
    quran_api_tafsir_scope: str = Field(default="content.tafsirs.read", validation_alias="QURAN_API_TAFSIR_SCOPE")
    quran_tafsir_resource_map: Dict[str, int] = Field(
        default_factory=lambda: {"ibn_kathir": 169},
        validation_alias="QURAN_TAFSIR_RESOURCE_MAP",
    )

    # AI Configuration
    llm_provider: Optional[str] = Field(default=None, validation_alias="LLM_PROVIDER")
    llm_api_key: Optional[str] = Field(default=None, validation_alias="LLM_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    llm_api_base_url: Optional[str] = Field(default=None, validation_alias="LLM_API_BASE_URL")
    llm_api_wire_api: Literal["chat_completions", "responses"] = Field(
        default="chat_completions",
        validation_alias="LLM_API_WIRE_API",
    )
    llm_model: Optional[str] = Field(default=None, validation_alias="LLM_MODEL")
    llm_max_tokens: int = Field(default=4000, validation_alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0, validation_alias="LLM_TEMPERATURE")

    @property
    def translation_api_key(self) -> Optional[str]:
        if self.llm_api_key:
            return self.llm_api_key
        if self.llm_api_base_url:
            try:
                host = urlsplit(self.llm_api_base_url).hostname
            except ValueError:
                return None
            if host != "api.openai.com":
                return None
        return self.openai_api_key

    # Embedding Configuration
    embedding_provider: Optional[str] = Field(default=None, validation_alias="EMBEDDING_PROVIDER")
    embedding_model: Optional[str] = Field(default=None, validation_alias="EMBEDDING_MODEL")
    embedding_api_key: Optional[str] = Field(default=None, validation_alias="EMBEDDING_API_KEY")
    embedding_api_base_url: Optional[str] = Field(
        default=None,
        validation_alias="EMBEDDING_API_BASE_URL",
    )
    embedding_dimensions: Optional[int] = Field(default=None, validation_alias="VECTOR_DIMENSIONS")
    embedding_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=120,
        validation_alias="EMBEDDING_TIMEOUT_SECONDS",
    )

    # Vector Database
    vector_db_url: Optional[str] = Field(default=None, validation_alias="VECTOR_DB_URL")
    vector_db_collection: str = Field(default="quran_tafsir", validation_alias="VECTOR_DB_COLLECTION")

    # Strapi CMS. These credentials are server-side only.
    strapi_api_base_url: Optional[str] = Field(
        default=None,
        validation_alias="STRAPI_API_BASE_URL",
    )
    strapi_api_token: Optional[str] = Field(default=None, validation_alias="STRAPI_API_TOKEN")

    # Security
    secret_key: str = Field(default="GENERATE_A_LONG_RANDOM_SECRET", validation_alias="SECRET_KEY")
    jwt_secret: str = Field(default="GENERATE_A_LONG_RANDOM_SECRET", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, validation_alias="JWT_EXPIRE_MINUTES")

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, validation_alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, validation_alias="RATE_LIMIT_PER_HOUR")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(default="json", validation_alias="LOG_FORMAT")

    # Monitoring
    metrics_port: int = Field(default=9090, validation_alias="METRICS_PORT")
    health_check_interval: int = Field(default=30, validation_alias="HEALTH_CHECK_INTERVAL")

    # QURAN AI specific settings
    default_language: str = Field(default="th", validation_alias="APP_DEFAULT_LOCALE")
    supported_languages: List[str] = Field(default=["th", "ar", "en"], validation_alias="APP_SUPPORTED_LOCALES")

settings = Settings()