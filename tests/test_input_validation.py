import csv
import os
import tempfile
from unittest.mock import patch

from src.football_calendar.validator import validate_inputs


class TestInputValidation:
    """Test input validation logic for command line arguments and file dependencies."""

    def test_valid_inputs_pass_validation(self):
        """Test that valid inputs pass validation without error."""
        # Create temporary directory and CSV file for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test_competitions.csv")
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NAME", "URL"])
                writer.writerow(["Premier League", "https://example.com/premier"])
                writer.writerow(["Championship", "https://example.com/championship"])

            # Should not raise any exception
            validate_inputs(temp_dir, 30, csv_file)
            validate_inputs(temp_dir, None, csv_file)  # None alert_minutes should be valid

    def test_output_directory_validation_errors(self):
        """Test various output directory validation errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test_competitions.csv")
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NAME", "URL"])
                writer.writerow(["Test League", "https://example.com/test"])

            # Test empty directory
            try:
                validate_inputs("", 30, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Output directory cannot be empty" in str(e)

            # Test None directory
            try:
                validate_inputs(None, 30, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Output directory cannot be empty" in str(e)

            # Test non-string directory
            try:
                validate_inputs(123, 30, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Output directory must be a string" in str(e)

            # Test non-existent directory
            try:
                validate_inputs("/this/path/does/not/exist", 30, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Output directory does not exist" in str(e)

            # Test directory that's actually a file
            temp_file = os.path.join(temp_dir, "not_a_directory")
            with open(temp_file, "w") as f:
                f.write("test")
            try:
                validate_inputs(temp_file, 30, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Output path is not a directory" in str(e)

    def test_readonly_directory_validation_error(self):
        """Test validation error for read-only directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test_competitions.csv")
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NAME", "URL"])
                writer.writerow(["Test League", "https://example.com/test"])

            readonly_dir = os.path.join(temp_dir, "readonly")
            os.makedirs(readonly_dir)

            # Mock the file writing to simulate permission error
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                try:
                    validate_inputs(readonly_dir, 30, csv_file)
                    raise AssertionError("Should have raised ValueError")
                except ValueError as e:
                    assert "Output directory is not writable" in str(e)

    def test_alert_minutes_validation_errors(self):
        """Test various alert minutes validation errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test_competitions.csv")
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NAME", "URL"])
                writer.writerow(["Test League", "https://example.com/test"])

            # Test non-integer alert minutes
            try:
                validate_inputs(temp_dir, "30", csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Alert minutes must be an integer" in str(e)

            # Test negative alert minutes
            try:
                validate_inputs(temp_dir, -5, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Alert minutes must be positive" in str(e)

            # Test zero alert minutes
            try:
                validate_inputs(temp_dir, 0, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Alert minutes must be positive" in str(e)

            # Test excessively large alert minutes (more than a week)
            try:
                validate_inputs(temp_dir, 20000, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Alert minutes seems too large" in str(e)

            # Test float instead of int
            try:
                validate_inputs(temp_dir, 30.5, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Alert minutes must be an integer" in str(e)

    def test_csv_file_validation_errors(self):
        """Test various CSV file validation errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test empty CSV file path
            try:
                validate_inputs(temp_dir, 30, "")
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Competitions file path cannot be empty" in str(e)

            # Test None CSV file path
            try:
                validate_inputs(temp_dir, 30, None)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Competitions file path cannot be empty" in str(e)

            # Test non-string CSV file path
            try:
                validate_inputs(temp_dir, 30, 123)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Competitions file path must be a string" in str(e)

            # Test non-existent CSV file
            try:
                validate_inputs(temp_dir, 30, "/this/file/does/not/exist.csv")
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Competitions file does not exist" in str(e)

            # Test directory instead of file
            try:
                validate_inputs(temp_dir, 30, temp_dir)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Competitions path is not a file" in str(e)

    def test_csv_content_validation_errors(self):
        """Test CSV file content validation errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test empty CSV file
            empty_csv = os.path.join(temp_dir, "empty.csv")
            with open(empty_csv, "w") as f:
                pass  # Create empty file
            try:
                validate_inputs(temp_dir, 30, empty_csv)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Competitions file appears to be empty" in str(e)

            # Test CSV missing NAME column
            no_name_csv = os.path.join(temp_dir, "no_name.csv")
            with open(no_name_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["URL", "OTHER"])
                writer.writerow(["https://example.com/test", "data"])
            try:
                validate_inputs(temp_dir, 30, no_name_csv)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "missing required 'NAME' column" in str(e)

            # Test CSV missing URL column
            no_url_csv = os.path.join(temp_dir, "no_url.csv")
            with open(no_url_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NAME", "OTHER"])
                writer.writerow(["Test League", "data"])
            try:
                validate_inputs(temp_dir, 30, no_url_csv)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "missing required 'URL' column" in str(e)

            # Test CSV with headers but no data
            no_data_csv = os.path.join(temp_dir, "no_data.csv")
            with open(no_data_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NAME", "URL"])
                # No data rows
            try:
                validate_inputs(temp_dir, 30, no_data_csv)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "contains no data rows" in str(e)

            # Test invalid CSV format is handled gracefully
            # Note: Python's csv module is quite forgiving, so this test focuses on
            # ensuring we can handle any CSV errors that might arise
            pass  # CSV format validation is covered by other tests

    def test_csv_permission_error(self):
        """Test CSV file permission errors by testing file that exists but has a different issue."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create CSV file in a subdirectory we'll make non-readable
            csv_subdir = os.path.join(temp_dir, "csv_dir")
            os.makedirs(csv_subdir)
            csv_file = os.path.join(csv_subdir, "test.csv")

            with open(csv_file, "w") as f:
                f.write("NAME,URL\n")

            # Change directory permissions to make file unreadable
            try:
                os.chmod(csv_subdir, 0o000)  # No permissions
                validate_inputs(temp_dir, 30, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                # Should get permission error or file not found (depending on OS)
                assert "Cannot read competitions file" in str(e) or "Competitions file does not exist" in str(e)
            finally:
                # Restore permissions for cleanup
                os.chmod(csv_subdir, 0o755)

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are collected and reported."""
        try:
            validate_inputs("/nonexistent", -5, "/nonexistent.csv")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            error_str = str(e)
            assert "Output directory does not exist" in error_str
            assert "Alert minutes must be positive" in error_str
            assert "Competitions file does not exist" in error_str
            # Check that it's formatted as a list
            assert "Input validation failed:" in error_str
            assert "  - " in error_str

    def test_boundary_values_for_alert_minutes(self):
        """Test boundary values for alert minutes validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test_competitions.csv")
            with open(csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NAME", "URL"])
                writer.writerow(["Test League", "https://example.com/test"])

            # Test minimum valid value
            validate_inputs(temp_dir, 1, csv_file)  # Should pass

            # Test maximum valid value (1 week = 10080 minutes)
            validate_inputs(temp_dir, 10080, csv_file)  # Should pass

            # Test just over maximum
            try:
                validate_inputs(temp_dir, 10081, csv_file)
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Alert minutes seems too large" in str(e)
