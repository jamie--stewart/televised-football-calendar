"""Settings management for the televised football calendar."""

import os
from typing import Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and CLI arguments."""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, env_prefix="FC_")

    # Competition configuration
    competitions_file: Optional[str] = Field(
        default=None, description="Path to competitions TOML file (default: competitions.toml in script directory)"
    )

    # Alert settings
    alert_minutes: Optional[int] = Field(default=None, description="Number of minutes before kick-off for alerts")

    # Output settings
    output_dir: Optional[str] = Field(default=None, description="Directory to save .ics files")

    # Dropbox settings
    dropbox_access_token: Optional[str] = Field(
        default=None, description="Dropbox access token for uploading calendar files"
    )

    dropbox_upload_path: str = Field(default="/", description="Path in Dropbox where calendar files should be uploaded")

    dropbox_enabled: bool = Field(default=False, description="Whether Dropbox upload is enabled")

    @field_validator("competitions_file")
    @classmethod
    def validate_competitions_file(cls, v: Optional[str]) -> Optional[str]:
        """Validate competitions file exists if specified."""
        if v is not None and not os.path.isfile(v):
            raise ValueError(f"Competitions file does not exist: {v}")
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Optional[str]) -> Optional[str]:
        """Validate output directory exists and is writable if specified."""
        if v is not None:
            if not os.path.exists(v):
                raise ValueError(f"Output directory does not exist: {v}")
            if not os.path.isdir(v):
                raise ValueError(f"Output path is not a directory: {v}")
            if not os.access(v, os.W_OK):
                raise ValueError(f"Output directory is not writable: {v}")
        return v

    @field_validator("alert_minutes")
    @classmethod
    def validate_alert_minutes(cls, v: Optional[int]) -> Optional[int]:
        """Validate alert minutes is within reasonable bounds if specified."""
        if v is not None and (v < 1 or v > 10080):  # 1 minute to 1 week
            raise ValueError(f"Alert minutes must be between 1 and 10080, got: {v}")
        return v

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


def load_settings(**cli_overrides) -> Settings:
    """
    Load application settings from environment variables and CLI arguments.

    Args:
        **cli_overrides: CLI arguments to override environment settings

    Returns:
        Settings: Merged settings with CLI arguments taking priority
    """
    # Filter out None values from CLI overrides
    filtered_overrides = {k: v for k, v in cli_overrides.items() if v is not None}

    # Use Pydantic's built-in validation with direct instantiation
    # CLI args passed directly will override environment variables
    return Settings(**filtered_overrides)
