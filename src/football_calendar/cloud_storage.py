"""Cloud storage integration for the televised football calendar."""

import logging
import os
import time
from typing import Optional

import dropbox
from dropbox.exceptions import ApiError, AuthError

logger = logging.getLogger(__name__)


class DropboxUploader:
    """Handles uploading calendar files to Dropbox."""

    def __init__(self, access_token: str, upload_path: str = "/"):
        """
        Initialize the Dropbox uploader.

        Args:
            access_token: Dropbox access token for authentication
            upload_path: Base path in Dropbox for uploads (default: root)
        """
        self.access_token = access_token
        self.upload_path = upload_path.rstrip("/")  # Remove trailing slash
        self.client = dropbox.Dropbox(access_token)

    def upload_file(self, local_file_path: str, remote_filename: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Upload a file to Dropbox with retry logic.

        Args:
            local_file_path: Path to the local file to upload
            remote_filename: Name for the file in Dropbox (defaults to local filename)

        Returns:
            tuple[bool, Optional[str]]: (upload_success, public_download_url)
        """
        if not os.path.exists(local_file_path):
            logger.error(f"Local file does not exist: {local_file_path}")
            return False, None

        if remote_filename is None:
            remote_filename = os.path.basename(local_file_path)

        remote_path = f"{self.upload_path}/{remote_filename}".replace("//", "/")

        logger.info(f"Uploading {local_file_path} to Dropbox as {remote_path}")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(local_file_path, "rb") as file:
                    file_content = file.read()

                # For files under 150MB, use simple upload
                if len(file_content) < 150 * 1024 * 1024:  # 150MB
                    self.client.files_upload(
                        file_content, remote_path, mode=dropbox.files.WriteMode.overwrite, autorename=False
                    )
                else:
                    # For larger files, use upload session (though calendar files should be small)
                    self._upload_large_file(file_content, remote_path)

                logger.info(f"Successfully uploaded {remote_filename} to Dropbox")

                # Get public download URL
                public_url = self.get_public_url(remote_path)
                return True, public_url

            except AuthError as e:
                logger.error(f"Dropbox authentication failed: {e}")
                return False, None  # Don't retry auth errors

            except ApiError as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Dropbox API error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to upload to Dropbox after {max_retries} attempts: {e}")
                    return False, None

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"Unexpected error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to upload to Dropbox after {max_retries} attempts: {e}")
                    return False, None

        return False, None

    def _upload_large_file(self, file_content: bytes, remote_path: str) -> None:
        """
        Upload a large file using Dropbox upload session.

        Args:
            file_content: File content as bytes
            remote_path: Destination path in Dropbox
        """
        chunk_size = 4 * 1024 * 1024  # 4MB chunks

        if len(file_content) <= chunk_size:
            # Small enough for simple upload
            self.client.files_upload(file_content, remote_path, mode=dropbox.files.WriteMode.overwrite)
            return

        # Start upload session
        session_start_result = self.client.files_upload_session_start(file_content[:chunk_size])
        cursor = dropbox.files.UploadSessionCursor(session_id=session_start_result.session_id, offset=chunk_size)

        # Upload remaining chunks
        for i in range(chunk_size, len(file_content), chunk_size):
            chunk = file_content[i : i + chunk_size]
            if i + chunk_size >= len(file_content):
                # Last chunk
                commit_info = dropbox.files.CommitInfo(path=remote_path, mode=dropbox.files.WriteMode.overwrite)
                self.client.files_upload_session_finish(chunk, cursor, commit_info)
            else:
                self.client.files_upload_session_append_v2(chunk, cursor)
                cursor.offset += len(chunk)

    def get_public_url(self, remote_path: str) -> Optional[str]:
        """
        Get or create a public download URL for a file in Dropbox.

        Args:
            remote_path: Path to the file in Dropbox

        Returns:
            Optional[str]: Public download URL if successful, None otherwise
        """
        try:
            # Try to get existing shared link first
            try:
                shared_links = self.client.sharing_list_shared_links(path=remote_path)
                if shared_links.links:
                    # Convert view link to direct download link
                    view_url = shared_links.links[0].url
                    download_url = view_url.replace("dropbox.com", "dl.dropboxusercontent.com").replace("dl=0", "dl=1")
                    return download_url
            except ApiError:
                # No existing shared link, create one
                pass

            # Create new shared link
            shared_link_metadata = self.client.sharing_create_shared_link_with_settings(
                path=remote_path,
                settings=dropbox.sharing.SharedLinkSettings(
                    requested_visibility=dropbox.sharing.RequestedVisibility.public
                ),
            )

            # Convert view link to direct download link
            view_url = shared_link_metadata.url
            download_url = view_url.replace("dropbox.com", "dl.dropboxusercontent.com").replace("dl=0", "dl=1")
            return download_url

        except ApiError as e:
            logger.error(f"Failed to create public URL for {remote_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating public URL for {remote_path}: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test the Dropbox connection and authentication.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            account_info = self.client.users_get_current_account()
            logger.info(f"Connected to Dropbox account: {account_info.name.display_name}")
            return True
        except AuthError:
            logger.error("Dropbox authentication failed - invalid access token")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Dropbox: {e}")
            return False


def upload_calendar_file(access_token: str, local_file_path: str, upload_path: str = "/") -> tuple[bool, Optional[str]]:
    """
    Convenience function to upload a single calendar file to Dropbox.

    Args:
        access_token: Dropbox access token
        local_file_path: Path to the local ICS file
        upload_path: Dropbox directory path for upload

    Returns:
        tuple[bool, Optional[str]]: (upload_success, public_download_url)
    """
    try:
        uploader = DropboxUploader(access_token, upload_path)
        return uploader.upload_file(local_file_path)
    except Exception as e:
        logger.error(f"Failed to upload calendar file: {e}")
        return False, None
