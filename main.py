"""Main entry point for the televised football calendar generator."""

import argparse
import csv
import logging
import sys

from generator import generate_calendar
from models import Competition
from scraper import get_fixtures_for_competition
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

    # Validate inputs
    competitions_file = get_competitions_file_path()
    try:
        validate_inputs(args.output_dir, args.alert_minutes, competitions_file)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
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

        except Exception as e:
            logger.error(f"Error processing competition {competition.name}: {e}")
            continue


if __name__ == "__main__":
    main()
