# Configuration management for QURAN AI API service

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Any, Optional
import os

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

    # AI Configuration
    llm_provider: Optional[str] = Field(default=None, validation_alias="LLM_PROVIDER")
    llm_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "LLM_API_KEY"),
    )
    llm_api_base_url: Optional[str] = Field(default=None, validation_alias="LLM_API_BASE_URL")
    llm_model: Optional[str] = Field(default=None, validation_alias="LLM_MODEL")
    llm_max_tokens: int = Field(default=4000, validation_alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0, validation_alias="LLM_TEMPERATURE")

    # Embedding Configuration
    embedding_provider: Optional[str] = Field(default=None, validation_alias="EMBEDDING_PROVIDER")
    embedding_model: Optional[str] = Field(default=None, validation_alias="EMBEDDING_MODEL")
    embedding_api_key: Optional[str] = Field(default=None, validation_alias="EMBEDDING_API_KEY")
    embedding_dimensions: Optional[int] = Field(default=None, validation_alias="VECTOR_DIMENSIONS")

    # Vector Database
    vector_db_url: Optional[str] = Field(default=None, validation_alias="VECTOR_DB_URL")
    vector_db_collection: str = Field(default="quran_tafsir", validation_alias="VECTOR_DB_COLLECTION")

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