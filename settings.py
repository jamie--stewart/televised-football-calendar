"""Settings management for the televised football calendar."""

from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, env_prefix="FC_")

    dropbox_access_token: Optional[str] = Field(
        default=None, description="Dropbox access token for uploading calendar files"
    )

    dropbox_upload_path: str = Field(default="/", description="Path in Dropbox where calendar files should be uploaded")

    dropbox_enabled: bool = Field(default=False, description="Whether Dropbox upload is enabled")

    @model_validator(mode="after")
    def validate_dropbox_settings(self) -> "Settings":
        """Validate Dropbox configuration when enabled."""
        if self.dropbox_enabled:
            if not self.dropbox_access_token:
                raise ValueError(
                    "Dropbox upload is enabled but FC_DROPBOX_ACCESS_TOKEN environment variable is not set. "
                    "Please set this in your .env file or environment."
                )

            # Validate upload path format
            if not self.dropbox_upload_path.startswith("/"):
                raise ValueError(f"Dropbox upload path must start with '/': {self.dropbox_upload_path}")

        return self


def load_settings() -> Settings:
    """Load application settings from environment variables."""
    return Settings()
