"""Tests for enhanced settings functionality."""

import os
import tempfile

import pytest

from src.football_calendar.settings import Settings, load_settings


@pytest.fixture
def temp_competitions_file():
    """Create a temporary competitions TOML file."""
    content = """
[competitions]

[competitions."Test League"]
url = "http://test.com/league"
start_date = ""
team_filters = []
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestEnhancedSettings:
    """Test enhanced settings with CLI and environment variable mixing."""

    def test_settings_with_valid_competitions_file(self, temp_competitions_file):
        """Test settings validation with valid competitions file."""
        settings = Settings(competitions_file=temp_competitions_file)
        assert settings.competitions_file == temp_competitions_file

    def test_settings_with_invalid_competitions_file(self):
        """Test settings validation with invalid competitions file."""
        with pytest.raises(ValueError, match="Competitions file does not exist"):
            Settings(competitions_file="/nonexistent/file.toml")

    def test_settings_with_valid_output_dir(self, temp_output_dir):
        """Test settings validation with valid output directory."""
        settings = Settings(output_dir=temp_output_dir)
        assert settings.output_dir == temp_output_dir

    def test_settings_with_invalid_output_dir(self):
        """Test settings validation with invalid output directory."""
        with pytest.raises(ValueError, match="Output directory does not exist"):
            Settings(output_dir="/nonexistent/directory")

    def test_settings_with_file_as_output_dir(self, temp_competitions_file):
        """Test settings validation when output_dir is a file, not directory."""
        with pytest.raises(ValueError, match="Output path is not a directory"):
            Settings(output_dir=temp_competitions_file)

    def test_settings_with_valid_alert_minutes(self):
        """Test settings validation with valid alert minutes."""
        settings = Settings(alert_minutes=30)
        assert settings.alert_minutes == 30

    def test_settings_with_invalid_alert_minutes_too_low(self):
        """Test settings validation with alert minutes too low."""
        with pytest.raises(ValueError, match="Alert minutes must be between 1 and 10080"):
            Settings(alert_minutes=0)

    def test_settings_with_invalid_alert_minutes_too_high(self):
        """Test settings validation with alert minutes too high."""
        with pytest.raises(ValueError, match="Alert minutes must be between 1 and 10080"):
            Settings(alert_minutes=20000)

    def test_cli_args_override_direct_instantiation(self, temp_output_dir, temp_competitions_file):
        """Test CLI arguments override when passed directly to Settings constructor."""
        settings = Settings(output_dir=temp_output_dir, competitions_file=temp_competitions_file, alert_minutes=30)

        assert settings.output_dir == temp_output_dir
        assert settings.competitions_file == temp_competitions_file
        assert settings.alert_minutes == 30

    def test_load_settings_with_cli_overrides(self, temp_output_dir):
        """Test load_settings function with CLI overrides."""
        settings = load_settings(output_dir=temp_output_dir, alert_minutes=45)

        assert settings.output_dir == temp_output_dir
        assert settings.alert_minutes == 45

    def test_load_settings_without_cli_overrides(self):
        """Test load_settings function without CLI overrides uses defaults."""
        settings = load_settings()

        # Should have default values (regardless of environment)
        assert settings.dropbox_upload_path == "/"
        # Note: dropbox_enabled might be True if FC_DROPBOX_ENABLED is set in environment

    def test_dropbox_settings_validation_enabled_without_token(self, monkeypatch):
        """Test Dropbox validation when enabled but no token provided."""
        # Clear any existing Dropbox token
        monkeypatch.delenv("FC_DROPBOX_ACCESS_TOKEN", raising=False)

        with pytest.raises(ValueError, match="FC_DROPBOX_ACCESS_TOKEN environment variable is not set"):
            Settings(dropbox_enabled=True, dropbox_access_token=None)

    def test_dropbox_settings_validation_invalid_path(self):
        """Test Dropbox validation with invalid upload path."""
        with pytest.raises(ValueError, match="Dropbox upload path must start with"):
            Settings(
                dropbox_enabled=True,
                dropbox_access_token="test_token",
                dropbox_upload_path="invalid/path",  # Missing leading slash
            )

    def test_dropbox_settings_validation_success(self):
        """Test successful Dropbox settings validation."""
        settings = Settings(dropbox_enabled=True, dropbox_access_token="test_token", dropbox_upload_path="/valid/path")

        assert settings.dropbox_enabled is True
        assert settings.dropbox_access_token == "test_token"
        assert settings.dropbox_upload_path == "/valid/path"

    def test_environment_variable_prefix(self, monkeypatch, temp_output_dir):
        """Test that environment variables with FC_ prefix are loaded."""
        monkeypatch.setenv("FC_OUTPUT_DIR", temp_output_dir)
        monkeypatch.setenv("FC_ALERT_MINUTES", "60")

        settings = Settings()

        assert settings.output_dir == temp_output_dir
        assert settings.alert_minutes == 60

    def test_cli_overrides_environment_variables(self, monkeypatch):
        """Test that CLI arguments override environment variables."""
        # Set environment variable
        monkeypatch.setenv("FC_ALERT_MINUTES", "30")

        # CLI should override environment
        settings = load_settings(alert_minutes=60)

        assert settings.alert_minutes == 60  # CLI value, not env var
