#  Generate a football calendar
import argparse
import csv
import logging
import os

# Remove unused datetime import since we use arrow for datetime handling
import sys
from datetime import timedelta

import arrow
import requests
from bs4 import BeautifulSoup
from ics.alarm import DisplayAlarm
from ics.icalendar import Calendar, Event
from user_agent import generate_user_agent

program = argparse.ArgumentParser(description="Generate an .ics file of the televised Premier League fixtures")
program.add_argument("output_dir", help="The absolute path to the directory to place the .ics files in")
program.add_argument("--alert-minutes", type=int, help="The number of minutes before kick-off that you want an alert")

headers = {
    "User-Agent": generate_user_agent(),
}

SRC_DIR = os.path.dirname(sys.argv[0])

logger = logging.getLogger(__name__)


def validate_inputs(output_dir, alert_minutes, competitions_file_path):
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


def _output_path(competition_name, output_dir):
    formatted_competition_name = competition_name.lower().strip().replace("'", "").replace(" ", "-")
    return os.path.join(output_dir, f"{formatted_competition_name}.ics")


def get_fixtures_for_competition(fixtures_url):
    logger.info(f"Getting games for competition: {fixtures_url}")
    logger.debug(f"Making HTTP request to: {fixtures_url}")

    fixtures_page = requests.get(fixtures_url, headers=headers)
    logger.debug(f"HTTP response status: {fixtures_page.status_code}")
    logger.debug(f"HTTP response content length: {len(fixtures_page.content)} bytes")

    soup = BeautifulSoup(fixtures_page.content, "html.parser")
    logger.debug("Parsed HTML with BeautifulSoup")

    listings_rows = soup.find_all("div", class_=["fixture", "fixture-date"])
    logger.debug(f"Found {len(listings_rows)} fixture and fixture-date rows")

    games = []

    match_date = None
    for row in listings_rows:
        if "fixture-date" in row.get("class", []):  # Have a new match date
            if "No Upcoming TV Fixtures" in row.text:
                logger.info(f"No games for competition {fixtures_url}")
                return games

            try:
                match_date = arrow.get(row.text, "dddd Do MMMM YYYY", tzinfo="Europe/London")
                logger.debug(f"Parsed match date: {match_date}")
            except (arrow.parser.ParserError, ValueError) as e:
                logger.warning(f'Failed to parse match date "{row.text}": {e}. Skipping this date.')
                continue

        else:  # This is a game
            try:
                fixture = ""

                # Parse team names with error handling
                teams_elem = row.find("div", class_="fixture__teams")
                if teams_elem is None:
                    logger.warning("No fixture__teams element found in row. Skipping fixture.")
                    continue

                teams_raw = teams_elem.get_text(strip=True)
                logger.debug(f'Raw teams text: "{teams_raw}"')

                if teams_raw.strip() == "TBC":
                    fixture = "TBC"
                elif " v " in teams_raw:
                    try:
                        home_team, away_team = [team.strip() for team in teams_raw.split(" v ")]
                        fixture = f"{home_team} vs {away_team}"
                        logger.debug(f"Parsed fixture: {fixture}")
                    except ValueError as e:
                        logger.warning(f'Failed to split team names "{teams_raw}": {e}. Skipping fixture.')
                        continue
                else:
                    logger.warning(f'Unrecognized team format "{teams_raw}". Skipping fixture.')
                    continue

                # Parse kickoff time with error handling
                time_elem = row.find("div", class_="fixture__time")
                if time_elem is None:
                    logger.warning("No fixture__time element found in row. Skipping fixture.")
                    continue

                kickoff_time_text = time_elem.get_text(strip=True)
                logger.debug(f'Raw time text: "{kickoff_time_text}"')

                if "TBC" in kickoff_time_text:
                    logger.debug(f"Time TBC for fixture {fixture}. Skipping.")
                    continue

                if match_date is None:
                    logger.warning(f"No match date available for fixture {fixture}. Skipping.")
                    continue

                try:
                    if ":" not in kickoff_time_text:
                        logger.warning(f'Invalid time format "{kickoff_time_text}" for fixture {fixture}. Skipping.')
                        continue
                    hour, minute = kickoff_time_text.split(":")
                    kick_off = match_date.replace(hour=int(hour), minute=int(minute))
                    logger.debug(f"Parsed kickoff time: {kick_off}")
                except (ValueError, TypeError) as e:
                    logger.warning(f'Failed to parse time "{kickoff_time_text}" for fixture {fixture}: {e}. Skipping.')
                    continue

                # Parse competition with error handling
                competition_elem = row.find("div", class_="fixture__competition")
                if competition_elem is None:
                    logger.warning(f'No fixture__competition element found for fixture {fixture}. Using "Unknown".')
                    competition = "Unknown"
                else:
                    try:
                        # Seem to have &nbsp; characters in their text
                        # ICS files are ascii-encoded
                        competition = (
                            competition_elem.get_text(strip=True)
                            .replace("\xa0", " ")
                            .encode("ascii", "ignore")
                            .decode("ascii")
                        )
                        logger.debug(f'Parsed competition: "{competition}"')
                    except (UnicodeError, AttributeError) as e:
                        logger.warning(f'Failed to parse competition for fixture {fixture}: {e}. Using "Unknown".')
                        competition = "Unknown"

                # Parse channel with error handling
                channels_elem = row.find("div", class_="fixture__channel")
                if channels_elem is None:
                    logger.warning(f'No fixture__channel element found for fixture {fixture}. Using "Unknown".')
                    channel = "Unknown"
                else:
                    try:
                        channels_text_raw = channels_elem.get_text(separator=" | ", strip=True).lower()
                        logger.debug(f'Raw channel text: "{channels_text_raw}"')

                        if "sky" in channels_text_raw:
                            channel = "Sky Sports"
                        elif "bbc" in channels_text_raw:
                            channel = "BBC"
                        elif "tnt sports" in channels_text_raw:
                            channel = "TNT Sports"
                        elif "itv" in channels_text_raw:
                            channel = "ITV"
                        elif "tbc" in channels_text_raw:
                            channel = "TBC"
                        elif "premier" in channels_text_raw:
                            channel = "Premier Sports"
                        elif "eleven" in channels_text_raw:
                            channel = "Eleven Sports"
                        elif "amazon prime video" in channels_text_raw:
                            channel = "Amazon Prime"
                        elif "s4c facebook" in channels_text_raw:
                            channel = "S4C Facebook"
                        elif "rangers tv" in channels_text_raw:
                            channel = "Rangers TV"
                        elif "celtic" in channels_text_raw:
                            channel = "Celtic TV"
                        else:
                            logger.warning(
                                f'Unrecognized television channel "{channels_text_raw}" for fixture {fixture}. Using "Unknown".'
                            )
                            channel = "Unknown"
                    except (AttributeError, TypeError) as e:
                        logger.warning(f'Failed to parse channel for fixture {fixture}: {e}. Using "Unknown".')
                        channel = "Unknown"

                logger.debug(f"Mapped to channel: {channel}")

                # Create the game object
                game = {"fixture": fixture, "kick_off": kick_off, "channel": channel, "competition": competition}
                games.append(game)
                logger.debug(f"Added game: {fixture} at {kick_off} on {channel}")

            except Exception as e:
                logger.error(f"Unexpected error parsing fixture row: {e}. Skipping this fixture.")
                continue

    logger.debug(f"Returning {len(games)} total games")
    return games


def generate_calendar_for_games(games_array, alert_minutes=None):
    calendar = Calendar()

    for game in games_array:
        event = Event()
        event.name = f"{game['fixture']} ({game['competition']})"
        start = game["kick_off"]
        event.begin = start
        event.end = start.shift(hours=+2)
        event.location = game["channel"]
        if alert_minutes:
            alarm = DisplayAlarm(trigger=timedelta(minutes=alert_minutes))
            event.alarms.append(alarm)
        calendar.events.add(event)

    return calendar


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    args = program.parse_args()

    # Validate all inputs before processing
    competitions_file = os.path.join(SRC_DIR, "competitions.csv")
    try:
        validate_inputs(args.output_dir, args.alert_minutes, competitions_file)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    with open(competitions_file) as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            games = get_fixtures_for_competition(row["URL"])
            logger.info(f"Got {len(games)} games for {row['NAME']}")

            output_path = _output_path(row["NAME"], args.output_dir)
            with open(output_path, "w") as ics_file:
                logger.info(f"Writing games to {output_path}")
                calendar = generate_calendar_for_games(games, args.alert_minutes)
                ics_file.writelines(calendar.serialize())
