"""Configuration Management"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Load environment variables with priority: .env.local > .env
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir / ".env.local", override=True)


class Config(BaseSettings):
    """Application Configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Configuration
    app_name: str = Field(default="BeanFlow Payroll Backend", validation_alias="APP_NAME")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # CORS Configuration
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias="ALLOWED_ORIGINS",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # Supabase Configuration
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_key: str = Field(..., validation_alias="SUPABASE_KEY")
    supabase_jwt_secret: str = Field(..., validation_alias="SUPABASE_JWT_SECRET")
    # Service role key for admin operations (inviting users, etc.)
    supabase_service_role_key: str | None = Field(
        default=None, validation_alias="SUPABASE_SERVICE_ROLE_KEY"
    )

    # Encryption Key (for SIN encryption in Phase 1+)
    # Optional - only needed when storing employee SIN numbers
    encryption_key: str | None = Field(default=None, validation_alias="ENCRYPTION_KEY")

    # Frontend URLs
    frontend_url: str = Field(
        default="http://localhost:5174", validation_alias="VITE_FRONTEND_URL"
    )

    # DigitalOcean Spaces Configuration
    do_spaces_endpoint: str = Field(
        default="nyc3.digitaloceanspaces.com", validation_alias="DO_SPACES_ENDPOINT"
    )
    do_spaces_access_key: str = Field(default="", validation_alias="DO_SPACES_ACCESS_KEY")
    do_spaces_secret_key: str = Field(default="", validation_alias="DO_SPACES_SECRET_KEY")
    do_spaces_bucket: str = Field(default="", validation_alias="DO_SPACES_BUCKET")
    do_spaces_region: str = Field(default="nyc3", validation_alias="DO_SPACES_REGION")
    do_spaces_root_prefix: str = Field(
        default="Beanflow-Payroll", validation_alias="DO_SPACES_ROOT_PREFIX"
    )

    # Email Configuration (Resend)
    resend_api_key: str | None = Field(default=None, validation_alias="RESEND_EMAIL_API_KEY")
    email_from_address: str = Field(
        default="noreply@email.beanflow.ai", validation_alias="EMAIL_FROM_ADDRESS"
    )
    email_from_name: str = Field(default="BeanFlow", validation_alias="EMAIL_FROM_NAME")


# Singleton pattern for configuration
_config: Config | None = None


def get_config() -> Config:
    """Get configuration singleton"""
    global _config
    if _config is None:
        _config = Config()  # type: ignore[call-arg]
        logger.info(f"Configuration loaded: {_config.app_name}")
    return _config
