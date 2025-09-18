"""Main entry point for the televised football calendar generator."""

import argparse
import csv
import logging
import sys

from cloud_storage import DropboxUploader
from generator import generate_calendar
from models import Competition
from scraper import get_fixtures_for_competition
from settings import load_settings
from utils import get_competitions_file_path, get_output_path, setup_logging
from validator import validate_inputs

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate an .ics file of the televised Premier League fixtures")
    parser.add_argument("output_dir", help="The absolute path to the directory to place the .ics files in")
    parser.add_argument(
        "--alert-minutes", type=int, help="The number of minutes before kick-off that you want an alert"
    )
    parser.add_argument("--upload-dropbox", action="store_true", help="Upload generated calendar files to Dropbox")
    parser.add_argument(
        "--dropbox-path",
        type=str,
        default="/",
        help="Path in Dropbox where calendar files should be uploaded (default: /)",
    )
    return parser.parse_args()


def load_competitions() -> list[Competition]:
    """Load competitions from the CSV file."""
    competitions_file = get_competitions_file_path()
    competitions = []

    with open(competitions_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            competition = Competition(name=row["NAME"], url=row["URL"])
            competitions.append(competition)

    return competitions


def main() -> None:
    """Main application entry point."""
    # Setup logging
    setup_logging()

    # Parse command line arguments
    args = parse_arguments()

    # Always load settings
    settings = load_settings()

    # Determine if Dropbox upload should be enabled
    dropbox_enabled = settings.dropbox_enabled or args.upload_dropbox

    # Handle CLI override behavior
    if args.upload_dropbox:
        if settings.dropbox_enabled:
            logger.warning(
                "Dropbox upload is already enabled via FC_DROPBOX_ENABLED environment variable. "
                "The --upload-dropbox flag is redundant."
            )
        else:
            logger.info("Dropbox upload enabled via --upload-dropbox flag")
            settings.dropbox_enabled = True

        # Override upload path if specified via CLI
        if args.dropbox_path != "/":
            settings.dropbox_upload_path = args.dropbox_path
    elif settings.dropbox_enabled:
        logger.info("Dropbox upload enabled via FC_DROPBOX_ENABLED environment variable")

    # Validate inputs
    competitions_file = get_competitions_file_path()
    try:
        validate_inputs(args.output_dir, args.alert_minutes, competitions_file)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    # Initialize Dropbox uploader if enabled
    dropbox_uploader = None
    if dropbox_enabled:
        try:
            dropbox_uploader = DropboxUploader(settings.dropbox_access_token, settings.dropbox_upload_path)
            logger.info("Dropbox uploader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Dropbox uploader: {e}")
            sys.exit(1)

    # Load competitions
    competitions = load_competitions()

    # Process each competition
    for competition in competitions:
        try:
            # Get fixtures for this competition
            fixtures = get_fixtures_for_competition(competition.url)
            logger.info(f"Got {len(fixtures)} fixtures for {competition.name}")

            # Generate calendar
            calendar = generate_calendar(fixtures, args.alert_minutes)

            # Write to file
            output_path = get_output_path(competition.name, args.output_dir)
            with open(output_path, "w") as ics_file:
                logger.info(f"Writing fixtures to {output_path}")
                ics_file.writelines(calendar.serialize())

            # Upload to Dropbox if enabled
            if dropbox_uploader:
                try:
                    upload_success, public_url = dropbox_uploader.upload_file(output_path)
                    if upload_success:
                        logger.info(f"Successfully uploaded {competition.name} calendar to Dropbox")
                        if public_url:
                            logger.info(f"Public download URL: {public_url}")
                        else:
                            logger.warning(f"Upload succeeded but could not generate public URL for {competition.name}")
                    else:
                        logger.warning(f"Failed to upload {competition.name} calendar to Dropbox")
                except Exception as upload_error:
                    logger.error(f"Error uploading {competition.name} to Dropbox: {upload_error}")
                    # Continue processing other competitions even if upload fails

        except Exception as e:
            logger.error(f"Error processing competition {competition.name}: {e}")
            continue


if __name__ == "__main__":
    main()
