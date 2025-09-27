"""Main entry point for the televised football calendar generator."""

import argparse
import logging
import os
import sys
from typing import Optional

from src.football_calendar.cloud_storage import DropboxUploader
from src.football_calendar.generator import generate_calendar
from src.football_calendar.models import Competition
from src.football_calendar.scraper import get_fixtures_for_competition
from src.football_calendar.settings import load_settings
from src.football_calendar.utils import (
    get_competitions_file_path,
    get_output_path,
    load_competitions_config,
    setup_logging,
    should_include_fixture,
)

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate an .ics file of the televised Premier League fixtures")
    parser.add_argument("output_dir", help="The absolute path to the directory to place the .ics files in")
    parser.add_argument(
        "--alert-minutes", type=int, help="The number of minutes before kick-off that you want an alert"
    )
    parser.add_argument(
        "--competitions-file",
        type=str,
        help="Path to competitions TOML file (default: competitions.toml in script directory)",
    )
    parser.add_argument("--upload-dropbox", action="store_true", help="Upload generated calendar files to Dropbox")
    parser.add_argument(
        "--dropbox-path",
        type=str,
        default=None,
        help="Path in Dropbox where calendar files should be uploaded (default: /)",
    )
    return parser.parse_args()


def load_competitions(competitions_file: Optional[str] = None) -> list[Competition]:
    """Load competitions from the TOML configuration file."""
    competitions_config = load_competitions_config(competitions_file)
    competitions = []

    for _alias, config in competitions_config.items():
        competition = Competition(
            name=config["name"],
            url=config["url"],
            start_date=config.get("start_date", ""),
            team_filters=config.get("team_filters", []),
        )
        competitions.append(competition)

    return competitions


def main() -> None:
    """Main application entry point."""
    # Setup logging
    setup_logging()

    # Parse command line arguments
    args = parse_arguments()

    # Load settings with CLI overrides
    try:
        settings = load_settings(
            output_dir=args.output_dir,
            alert_minutes=args.alert_minutes,
            competitions_file=args.competitions_file,
            dropbox_enabled=args.upload_dropbox,
            dropbox_upload_path=args.dropbox_path,
        )
    except ValueError as e:
        logger.error(f"Settings validation failed: {e}")
        sys.exit(1)

    # Handle CLI override behavior for Dropbox
    if args.upload_dropbox and "FC_DROPBOX_ENABLED" in os.environ:
        logger.warning(
            "Dropbox upload is already enabled via FC_DROPBOX_ENABLED environment variable. "
            "The --upload-dropbox flag is redundant."
        )
    elif args.upload_dropbox:
        logger.info("Dropbox upload enabled via --upload-dropbox flag")
    elif settings.dropbox_enabled:
        logger.info("Dropbox upload enabled via FC_DROPBOX_ENABLED environment variable")

    # Determine competitions file path
    competitions_file = settings.competitions_file or get_competitions_file_path()

    # Final validation for required settings
    if not settings.output_dir:
        logger.error("Output directory must be specified via CLI argument or FC_OUTPUT_DIR environment variable")
        sys.exit(1)

    # Initialize Dropbox uploader if enabled
    dropbox_uploader = None
    if settings.dropbox_enabled:
        try:
            dropbox_uploader = DropboxUploader(settings.dropbox_access_token, settings.dropbox_upload_path)
            logger.info("Dropbox uploader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Dropbox uploader: {e}")
            sys.exit(1)

    # Load competitions
    competitions = load_competitions(competitions_file)

    # Process each competition
    for competition in competitions:
        try:
            # Get fixtures for this competition
            all_fixtures = get_fixtures_for_competition(competition.url)
            logger.info(f"Got {len(all_fixtures)} raw fixtures for {competition.name}")

            # Apply filtering based on competition configuration
            competition_config = {"start_date": competition.start_date, "team_filters": competition.team_filters}

            fixtures = [
                fixture
                for fixture in all_fixtures
                if should_include_fixture(fixture.fixture, fixture.kick_off.datetime, competition_config)
            ]

            filtered_count = len(all_fixtures) - len(fixtures)
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} fixtures for {competition.name}")
            logger.info(f"Processing {len(fixtures)} fixtures for {competition.name}")

            # Generate calendar
            calendar = generate_calendar(fixtures, settings.alert_minutes)

            # Write to file
            output_path = get_output_path(competition.name, settings.output_dir)
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
