import os
from unittest.mock import MagicMock, patch

import pytest
from dropbox.exceptions import AuthError

from cloud_storage import DropboxUploader
from settings import Settings


class TestDropboxIntegration:
    """Test Dropbox cloud storage integration functionality."""

    @patch("cloud_storage.dropbox.Dropbox")
    def test_successful_dropbox_upload_happy_path(self, mock_dropbox_class, temp_output_dir):
        """Test successful Dropbox upload with valid configuration."""
        # Setup mock Dropbox client
        mock_client = MagicMock()
        mock_dropbox_class.return_value = mock_client

        # Mock successful upload
        mock_client.files_upload.return_value = MagicMock()

        # Mock sharing functionality for public URL
        mock_shared_link = MagicMock()
        mock_shared_link.url = "https://dropbox.com/s/abc123/test-calendar.ics?dl=0"
        mock_client.sharing_list_shared_links.return_value.links = [mock_shared_link]

        # Create a test ICS file
        test_file = os.path.join(temp_output_dir, "test-calendar.ics")
        with open(test_file, "w") as f:
            f.write("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR")

        # Test the upload using DropboxUploader
        uploader = DropboxUploader("test_token", "/test-path")
        success, public_url = uploader.upload_file(test_file)

        # Verify upload was successful
        assert success is True
        assert public_url == "https://dl.dropboxusercontent.com/s/abc123/test-calendar.ics?dl=1"

        # Verify Dropbox client was initialized with correct token
        mock_dropbox_class.assert_called_once_with("test_token")

        # Verify upload was called with correct parameters
        mock_client.files_upload.assert_called_once()
        args, _ = mock_client.files_upload.call_args
        uploaded_content, remote_path = args

        assert remote_path == "/test-path/test-calendar.ics"
        assert b"BEGIN:VCALENDAR" in uploaded_content

    @patch("cloud_storage.dropbox.Dropbox")
    def test_dropbox_upload_with_retry_logic(self, mock_dropbox_class, temp_output_dir):
        """Test that retry logic works for transient failures."""
        # Setup mock Dropbox client
        mock_client = MagicMock()
        mock_dropbox_class.return_value = mock_client

        # Mock first two calls to fail, third to succeed
        mock_client.files_upload.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            MagicMock(),  # Success on third try
        ]

        # Mock sharing functionality for public URL (after successful upload)
        mock_shared_link = MagicMock()
        mock_shared_link.url = "https://dropbox.com/s/def456/test-calendar.ics?dl=0"
        mock_client.sharing_list_shared_links.return_value.links = [mock_shared_link]

        # Create a test ICS file
        test_file = os.path.join(temp_output_dir, "test-calendar.ics")
        with open(test_file, "w") as f:
            f.write("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR")

        # Test the upload - should eventually succeed
        uploader = DropboxUploader("test_token", "/calendars")
        success, public_url = uploader.upload_file(test_file)

        # Verify upload eventually succeeded after retries
        assert success is True
        assert public_url == "https://dl.dropboxusercontent.com/s/def456/test-calendar.ics?dl=1"
        assert mock_client.files_upload.call_count == 3

    @patch("cloud_storage.dropbox.Dropbox")
    def test_dropbox_auth_failure(self, mock_dropbox_class):
        """Test that authentication failures are handled gracefully."""
        # Setup mock Dropbox client to raise AuthError
        mock_client = MagicMock()
        mock_dropbox_class.return_value = mock_client
        auth_error = AuthError("test_request_id", "Invalid access token")
        mock_client.users_get_current_account.side_effect = auth_error

        # Test connection should fail
        uploader = DropboxUploader("invalid_token")
        success = uploader.test_connection()

        assert success is False
        mock_dropbox_class.assert_called_once_with("invalid_token")

    @patch.dict(os.environ, {"FC_DROPBOX_ACCESS_TOKEN": "test_token", "FC_DROPBOX_ENABLED": "true"})
    def test_settings_validation_with_valid_token(self):
        """Test that settings validation passes with valid token."""
        # Should not raise an exception when creating Settings with valid config
        settings = Settings()
        assert settings.dropbox_enabled is True
        assert settings.dropbox_access_token == "test_token"

    def test_settings_validation_fails_without_token(self):
        """Test that settings validation fails when token is missing."""
        # Test the validation logic directly by creating Settings with conflicting values
        with pytest.raises(ValueError, match="FC_DROPBOX_ACCESS_TOKEN environment variable is not set"):
            Settings(dropbox_enabled=True, dropbox_access_token=None, dropbox_upload_path="/")

    @patch("cloud_storage.dropbox.Dropbox")
    def test_upload_failure_returns_false(self, mock_dropbox_class, temp_output_dir):
        """Test that upload failures return False and don't crash."""
        # Setup mock Dropbox client to always fail
        mock_client = MagicMock()
        mock_dropbox_class.return_value = mock_client
        mock_client.files_upload.side_effect = Exception("Permanent failure")

        # Create a test file
        test_file = os.path.join(temp_output_dir, "test-calendar.ics")
        with open(test_file, "w") as f:
            f.write("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR")

        # Test upload - should fail gracefully
        uploader = DropboxUploader("test_token")
        success, public_url = uploader.upload_file(test_file)

        assert success is False
        assert public_url is None  # Should not have a public URL on failure
        # Should have attempted retry 3 times
        assert mock_client.files_upload.call_count == 3
