"""Input validation functionality for the televised football calendar."""

import csv
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def validate_inputs(output_dir: str, alert_minutes: Optional[int], competitions_file_path: str) -> None:
    """
    Validate all user inputs and system requirements before processing.

    Args:
        output_dir (str): Directory path where ICS files will be written
        alert_minutes (int or None): Minutes before events to trigger alerts
        competitions_file_path (str): Path to the competitions CSV file

    Raises:
        ValueError: If any validation fails with a descriptive error message

    Returns:
        None: Validation passes silently if all checks succeed
    """
    errors = []

    # Validate output directory
    if not output_dir:
        errors.append("Output directory cannot be empty")
    elif not isinstance(output_dir, str):
        errors.append(f"Output directory must be a string, got {type(output_dir).__name__}")
    else:
        # Check if directory exists
        if not os.path.exists(output_dir):
            errors.append(f"Output directory does not exist: {output_dir}")
        elif not os.path.isdir(output_dir):
            errors.append(f"Output path is not a directory: {output_dir}")
        else:
            # Check if directory is writable
            test_file = os.path.join(output_dir, ".write_test")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                logger.debug(f"Output directory is writable: {output_dir}")
            except (OSError, PermissionError) as e:
                errors.append(f"Output directory is not writable: {output_dir} ({e})")

    # Validate alert minutes
    if alert_minutes is not None:
        if not isinstance(alert_minutes, int):
            errors.append(f"Alert minutes must be an integer, got {type(alert_minutes).__name__}")
        elif alert_minutes <= 0:
            errors.append(f"Alert minutes must be positive, got {alert_minutes}")
        elif alert_minutes > 10080:  # More than a week seems unreasonable
            errors.append(f"Alert minutes seems too large ({alert_minutes}), maximum is 10080 (1 week)")
        else:
            logger.debug(f"Alert minutes validated: {alert_minutes}")

    # Validate competitions CSV file
    if not competitions_file_path:
        errors.append("Competitions file path cannot be empty")
    elif not isinstance(competitions_file_path, str):
        errors.append(f"Competitions file path must be a string, got {type(competitions_file_path).__name__}")
    else:
        if not os.path.exists(competitions_file_path):
            errors.append(f"Competitions file does not exist: {competitions_file_path}")
        elif not os.path.isfile(competitions_file_path):
            errors.append(f"Competitions path is not a file: {competitions_file_path}")
        else:
            # Check if file is readable and has proper CSV structure
            try:
                with open(competitions_file_path) as csvfile:
                    reader = csv.DictReader(csvfile)
                    headers = reader.fieldnames
                    if not headers:
                        errors.append(f"Competitions file appears to be empty: {competitions_file_path}")
                    elif "NAME" not in headers:
                        errors.append(f"Competitions file missing required 'NAME' column: {competitions_file_path}")
                    elif "URL" not in headers:
                        errors.append(f"Competitions file missing required 'URL' column: {competitions_file_path}")
                    else:
                        # Count rows to ensure file has data
                        row_count = sum(1 for row in reader)
                        if row_count == 0:
                            errors.append(f"Competitions file contains no data rows: {competitions_file_path}")
                        else:
                            logger.debug(f"Competitions file validated: {row_count} competitions found")
            except (OSError, PermissionError) as e:
                errors.append(f"Cannot read competitions file: {competitions_file_path} ({e})")
            except csv.Error as e:
                errors.append(f"Invalid CSV format in competitions file: {competitions_file_path} ({e})")

    # If any errors were found, raise a comprehensive error message
    if errors:
        error_message = "Input validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        logger.error(error_message)
        raise ValueError(error_message)

    logger.info("All input validation checks passed")
