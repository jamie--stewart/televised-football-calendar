"""HTML parsing and data extraction for televised football fixtures."""

import logging

import arrow
from bs4 import BeautifulSoup

from constants import CHANNEL_MAPPINGS, DEFAULT_CHANNEL
from models import Fixture

logger = logging.getLogger(__name__)


def map_channel_name(channels_text_raw: str) -> str:
    """
    Map raw channel text to standardized channel names.

    Args:
        channels_text_raw (str): Raw channel text from HTML

    Returns:
        str: Standardized channel name
    """
    channels_text_lower = channels_text_raw.lower()

    for key, friendly_name in CHANNEL_MAPPINGS.items():
        if key in channels_text_lower:
            return friendly_name

    logger.warning(f'Unrecognized television channel "{channels_text_raw}". Using "{DEFAULT_CHANNEL}".')
    return DEFAULT_CHANNEL


def parse_fixtures_html(html_content: bytes, source_url: str) -> list[Fixture]:
    """
    Parse HTML content and extract fixtures.

    Args:
        html_content (bytes): Raw HTML content from the web page
        source_url (str): URL of the source (for logging purposes)

    Returns:
        List[Fixture]: List of parsed fixtures
    """
    soup = BeautifulSoup(html_content, "html.parser")
    logger.debug("Parsed HTML with BeautifulSoup")

    listings_rows = soup.find_all("div", class_=["fixture", "fixture-date"])
    logger.debug(f"Found {len(listings_rows)} fixture and fixture-date rows")

    fixtures = []
    match_date = None

    for row in listings_rows:
        if "fixture-date" in row.get("class", []):  # Have a new match date
            if "No Upcoming TV Fixtures" in row.text:
                logger.info(f"No games for competition {source_url}")
                return fixtures

            try:
                match_date = arrow.get(row.text, "dddd Do MMMM YYYY", tzinfo="Europe/London")
                logger.debug(f"Parsed match date: {match_date}")
            except (arrow.parser.ParserError, ValueError) as e:
                logger.warning(f'Failed to parse match date "{row.text}": {e}. Skipping this date.')
                continue

        else:  # This is a game
            try:
                fixture_name = ""

                # Parse team names with error handling
                teams_elem = row.find("div", class_="fixture__teams")
                if teams_elem is None:
                    logger.warning("No fixture__teams element found in row. Skipping fixture.")
                    continue

                teams_raw = teams_elem.get_text(strip=True)
                logger.debug(f'Raw teams text: "{teams_raw}"')

                if teams_raw.strip() == "TBC":
                    fixture_name = "TBC"
                elif " v " in teams_raw:
                    try:
                        home_team, away_team = [team.strip() for team in teams_raw.split(" v ")]
                        fixture_name = f"{home_team} vs {away_team}"
                        logger.debug(f"Parsed fixture: {fixture_name}")
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
                    logger.debug(f"Time TBC for fixture {fixture_name}. Skipping.")
                    continue

                if match_date is None:
                    logger.warning(f"No match date available for fixture {fixture_name}. Skipping.")
                    continue

                try:
                    if ":" not in kickoff_time_text:
                        logger.warning(
                            f'Invalid time format "{kickoff_time_text}" for fixture {fixture_name}. Skipping.'
                        )
                        continue
                    hour, minute = kickoff_time_text.split(":")
                    kick_off = match_date.replace(hour=int(hour), minute=int(minute))
                    logger.debug(f"Parsed kickoff time: {kick_off}")
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f'Failed to parse time "{kickoff_time_text}" for fixture {fixture_name}: {e}. Skipping.'
                    )
                    continue

                # Parse competition with error handling
                competition_elem = row.find("div", class_="fixture__competition")
                if competition_elem is None:
                    logger.warning(
                        f'No fixture__competition element found for fixture {fixture_name}. Using "Unknown".'
                    )
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
                        logger.warning(f'Failed to parse competition for fixture {fixture_name}: {e}. Using "Unknown".')
                        competition = "Unknown"

                # Parse channel with error handling
                channels_elem = row.find("div", class_="fixture__channel")
                if channels_elem is None:
                    logger.warning(f'No fixture__channel element found for fixture {fixture_name}. Using "Unknown".')
                    channel = "Unknown"
                else:
                    try:
                        channels_text_raw = channels_elem.get_text(separator=" | ", strip=True)
                        logger.debug(f'Raw channel text: "{channels_text_raw}"')
                        channel = map_channel_name(channels_text_raw)
                    except (AttributeError, TypeError) as e:
                        logger.warning(f'Failed to parse channel for fixture {fixture_name}: {e}. Using "Unknown".')
                        channel = "Unknown"

                logger.debug(f"Mapped to channel: {channel}")

                # Create the Fixture object
                fixture = Fixture(fixture=fixture_name, kick_off=kick_off, channel=channel, competition=competition)
                fixtures.append(fixture)
                logger.debug(f"Added fixture: {fixture_name} at {kick_off} on {channel}")

            except Exception as e:
                logger.error(f"Unexpected error parsing fixture row: {e}. Skipping this fixture.")
                continue

    logger.debug(f"Returning {len(fixtures)} total fixtures")
    return fixtures
