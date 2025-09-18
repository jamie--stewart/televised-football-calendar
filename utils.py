"""Utility functions for the televised football calendar."""

import logging
import os
import re
import sys
from datetime import datetime
from typing import Optional

import tomllib


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_output_path(competition_name: str, output_dir: str) -> str:
    """
    Generate output file path for a competition's ICS file.

    Args:
        competition_name (str): Name of the competition
        output_dir (str): Directory to save the file in

    Returns:
        str: Full path to the output ICS file
    """
    formatted_competition_name = competition_name.lower().strip().replace("'", "").replace(" ", "-")
    return os.path.join(output_dir, f"{formatted_competition_name}.ics")


def get_script_directory() -> str:
    """
    Get the directory containing the main script.

    Returns:
        str: Directory path where the script is located
    """
    return os.path.dirname(sys.argv[0])


def get_competitions_file_path() -> str:
    """
    Get the path to the competitions.toml file.

    Returns:
        str: Full path to the competitions.toml file
    """
    return os.path.join(get_script_directory(), "competitions.toml")


def load_competitions_config(competitions_file: Optional[str] = None) -> dict[str, dict[str, any]]:
    """
    Load competitions configuration from TOML file.

    Args:
        competitions_file (Optional[str]): Path to competitions file. If None, uses default.

    Returns:
        Dict[str, Dict[str, any]]: Competition configurations
    """
    if competitions_file is None:
        competitions_file = get_competitions_file_path()

    try:
        with open(competitions_file, "rb") as f:
            config = tomllib.load(f)
        return config.get("competitions", {})
    except FileNotFoundError:
        logging.error(f"Competitions file not found: {competitions_file}")
        return {}
    except tomllib.TOMLDecodeError as e:
        logging.error(f"Error parsing TOML file: {e}")
        return {}


def should_include_fixture(fixture_name: str, kick_off: datetime, competition_config: dict[str, any]) -> bool:
    """
    Check if a fixture should be included based on competition configuration.

    Args:
        fixture_name (str): Name of the fixture (e.g., "Team A vs Team B")
        kick_off (datetime): Kickoff time of the fixture
        competition_config (Dict[str, any]): Competition configuration

    Returns:
        bool: True if the fixture should be included
    """
    # Check date filtering
    start_date_str = competition_config.get("start_date", "")
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if kick_off.date() < start_date:
                return False
        except ValueError:
            logging.warning(f"Invalid start_date format in competition config: {start_date_str}")

    # Check team filtering
    team_filters = competition_config.get("team_filters", [])
    if team_filters and fixture_name != "TBC":
        # Extract team names from fixture (handles "Team A vs Team B" format)
        teams = [team.strip() for team in fixture_name.split(" vs ")] if " vs " in fixture_name else [fixture_name]

        # Check if any team matches any of the regex patterns
        for team in teams:
            for pattern in team_filters:
                try:
                    if re.search(pattern, team, re.IGNORECASE):
                        return True
                except re.error:
                    logging.warning(f"Invalid regex pattern in team_filters: {pattern}")

        # If team filters are specified but no teams match, exclude the fixture
        return False

    return True
