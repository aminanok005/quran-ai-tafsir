# Configuration management for QURAN AI API service

from pydantic import BaseSettings, Field
from typing import List, Dict, Any, Optional
import os

class Settings(BaseSettings):
    # App settings
    app_name: str = "QURAN AI API"
    version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_timeout: int = Field(default=30, env="DATABASE_TIMEOUT")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_pool_size: int = Field(default=10, env="REDIS_POOL_SIZE")
    redis_timeout: int = Field(default=5, env="REDIS_TIMEOUT")

    # Quran Foundation API
    quran_api_base_url: str = Field(default="https://apis.quran.foundation", env="QURAN_API_BASE_URL")
    quran_api_client_id: str = Field(default="REPLACE_WITH_APPROVED_CLIENT_ID", env="QURAN_API_CLIENT_ID")
    quran_api_client_secret: str = Field(default="REPLACE_WITH_SECRET", env="QURAN_API_CLIENT_SECRET")
    quran_api_token_cache_ttl: int = Field(default=3300, env="QURAN_API_TOKEN_CACHE_TTL_SECONDS")

    # AI Configuration
    llm_provider: str = Field(default="OPENAI", env="LLM_PROVIDER")
    llm_api_key: str = Field(default="REPLACE_ME", env="LLM_API_KEY")
    llm_api_base_url: Optional[str] = Field(default=None, env="LLM_API_BASE_URL")
    llm_model: str = Field(default="gpt-4o", env="LLM_MODEL")
    llm_max_tokens: int = Field(default=4000, env="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0, env="LLM_TEMPERATURE")

    # Embedding Configuration
    embedding_provider: str = Field(default="OPENAI", env="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    embedding_api_key: str = Field(default="REPLACE_ME", env="EMBEDDING_API_KEY")
    embedding_dimensions: int = Field(default=1536, env="VECTOR_DIMENSIONS")

    # Vector Database
    vector_db_url: Optional[str] = Field(default=None, env="VECTOR_DB_URL")
    vector_db_collection: str = Field(default="quran_tafsir", env="VECTOR_DB_COLLECTION")

    # Security
    secret_key: str = Field(default="GENERATE_A_LONG_RANDOM_SECRET", env="SECRET_KEY")
    jwt_secret: str = Field(default="GENERATE_A_LONG_RANDOM_SECRET", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, env="JWT_EXPIRE_MINUTES")

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    # Monitoring
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    # QURAN AI specific settings
    default_language: str = Field(default="th", env="APP_DEFAULT_LOCALE")
    supported_languages: List[str] = Field(default=["th", "ar", "en"], env="APP_SUPPORTED_LOCALES")

    class Config:
        env_file = ".env"
        case_sensitive = False

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return init_settings, env_settings, file_secret_settings

settings = Settings()