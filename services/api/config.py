# Configuration management for QURAN AI API service

import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            REPOSITORY_ROOT / ".env",
            REPOSITORY_ROOT / ".env.local",
        ),
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
    cors_origins: Annotated[List[str], NoDecode] = Field(
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
    quran_api_tafsir_cache_ttl: int = Field(
        default=300,
        ge=0,
        le=3600,
        validation_alias="QURAN_API_TAFSIR_CACHE_TTL_SECONDS",
    )
    quran_api_auth_base_url: Optional[str] = Field(default=None, validation_alias="QURAN_API_AUTH_BASE_URL")
    quran_api_tafsir_scope: str = Field(default="content.tafsirs.read", validation_alias="QURAN_API_TAFSIR_SCOPE")
    quran_tafsir_resource_map: Dict[str, int] = Field(
        default_factory=lambda: {"ibn_kathir": 168},
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

    # Text-to-speech settings are deliberately independent from LLM credentials and models.
    tts_enabled: bool = Field(default=False, validation_alias="TTS_ENABLED")
    tts_api_key: Optional[str] = Field(default=None, validation_alias="TTS_API_KEY")
    tts_model: Optional[str] = Field(default=None, validation_alias="TTS_MODEL")
    tts_api_base_url: Optional[str] = Field(default=None, validation_alias="TTS_API_BASE_URL")
    tts_allowed_editions: Annotated[List[str], NoDecode] = Field(
        default_factory=list,
        validation_alias="TTS_ALLOWED_EDITIONS",
    )
    tts_voice_map: Dict[str, str] = Field(default_factory=dict, validation_alias="TTS_VOICE_MAP")
    tts_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=120,
        validation_alias="TTS_TIMEOUT_SECONDS",
    )
    tts_max_text_chars: int = Field(
        default=5000,
        ge=1,
        le=100000,
        validation_alias="TTS_MAX_TEXT_CHARS",
    )
    tts_max_audio_bytes: int = Field(
        default=10000000,
        ge=1,
        le=100000000,
        validation_alias="TTS_MAX_AUDIO_BYTES",
    )
    tts_max_source_bytes: int = Field(
        default=2000000,
        ge=1,
        le=100000000,
        validation_alias="TTS_MAX_SOURCE_BYTES",
    )
    tts_cache_max_bytes: int = Field(
        default=50000000,
        ge=1,
        le=1000000000,
        validation_alias="TTS_CACHE_MAX_BYTES",
    )
    tts_cache_ttl_seconds: int = Field(
        default=300,
        ge=1,
        le=86400,
        validation_alias="TTS_CACHE_TTL_SECONDS",
    )
    tts_rate_limit_per_minute: int = Field(
        default=30,
        ge=1,
        le=1000,
        validation_alias="TTS_RATE_LIMIT_PER_MINUTE",
    )

    @field_validator("tts_api_base_url")
    @classmethod
    def validate_tts_api_base_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        try:
            parsed_url = urlsplit(value)
            host = parsed_url.hostname
            _ = parsed_url.port
        except ValueError as error:
            raise ValueError(
                "TTS API base URL must be a valid HTTPS URL or loopback HTTP URL"
            ) from error

        if not host or parsed_url.scheme.lower() not in {"https", "http"}:
            raise ValueError("TTS API base URL must be a valid HTTPS URL or loopback HTTP URL")
        if parsed_url.scheme.lower() == "http" and host not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("TTS API base URL must use HTTPS except for recognized loopback hosts")
        return value

    @field_validator("tts_allowed_editions")
    @classmethod
    def validate_tts_allowed_editions(cls, value: List[str]) -> List[str]:
        supported_editions = {"th.thai", "en.sahih", "id.indonesian"}
        unknown_editions = set(value) - supported_editions
        if unknown_editions:
            raise ValueError(f"Unsupported TTS editions: {', '.join(sorted(unknown_editions))}")
        return value

    @field_validator("tts_voice_map")
    @classmethod
    def validate_tts_voice_map(cls, value: Dict[str, str]) -> Dict[str, str]:
        supported_languages = {"th", "en", "id"}
        unknown_languages = set(value) - supported_languages
        if unknown_languages:
            raise ValueError(
                f"Unsupported TTS voice languages: {', '.join(sorted(unknown_languages))}"
            )
        if any(not voice.strip() for voice in value.values()):
            raise ValueError("TTS voice names must not be empty")
        return value

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
    supported_languages: Annotated[List[str], NoDecode] = Field(
        default=["th", "ar", "en"],
        validation_alias="APP_SUPPORTED_LOCALES",
    )

    @field_validator("cors_origins", "supported_languages", "tts_allowed_editions", mode="before")
    @classmethod
    def parse_string_lists(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if normalized.startswith("["):
            return json.loads(normalized)
        return [item.strip() for item in normalized.split(",") if item.strip()]

settings = Settings()
