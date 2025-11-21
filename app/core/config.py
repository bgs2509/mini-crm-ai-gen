"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables.
"""
from typing import Annotated, List
import json
from pydantic import Field, field_validator, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_string_list(v: str | list[str]) -> list[str]:
    """
    Parse list from string or list.

    Supports both comma-separated strings and JSON arrays.
    This allows flexible configuration in .env files.

    Args:
        v: String or list value

    Returns:
        List of strings

    Examples:
        "a,b,c" → ["a", "b", "c"]
        ["a", "b"] → ["a", "b"]
        '["a","b"]' → ["a", "b"]
    """
    if isinstance(v, str):
        # Remove whitespace
        v = v.strip()

        # Try to parse as JSON array first
        if v.startswith('[') and v.endswith(']'):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass

        # Split by comma
        return [item.strip() for item in v.split(",") if item.strip()]

    return v


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://crm_user:crm_password@localhost:5432/crm_db",
        description="PostgreSQL database URL"
    )
    db_pool_size: int = Field(default=5, ge=1, description="Database connection pool size")
    db_max_overflow: int = Field(default=10, ge=0, description="Max overflow connections")
    db_pool_pre_ping: bool = Field(default=True, description="Enable pool pre-ping")
    db_echo: bool = Field(default=False, description="Echo SQL queries")

    # JWT Authentication
    secret_key: str = Field(
        default="change-me-in-production-minimum-32-characters",
        min_length=32,
        description="Secret key for JWT"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=15,
        ge=1,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        description="Refresh token expiration in days"
    )

    # Security
    bcrypt_rounds: int = Field(default=12, ge=4, le=31, description="BCrypt rounds")

    # Cache (In-Memory)
    cache_ttl_seconds: int = Field(default=300, ge=0, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, ge=0, description="Maximum cache size")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, ge=1, description="Rate limit per minute")

    # CORS
    cors_origins: Annotated[
        List[str],
        BeforeValidator(parse_string_list)
    ] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")

    # Default Currency
    default_currency: str = Field(default="USD", description="Default currency code")

    # Supported Currencies (ISO 4217 codes)
    supported_currencies: Annotated[
        List[str],
        BeforeValidator(parse_string_list)
    ] = Field(
        default=["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "RUB"],
        description="List of supported currency codes"
    )

    @field_validator("default_currency")
    @classmethod
    def validate_default_currency(cls, v: str) -> str:
        """Validate default currency is uppercase."""
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() == "testing"


# Global settings instance
settings = Settings()
