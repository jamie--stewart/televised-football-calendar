"""Utility functions for the televised football calendar."""

import logging
import os
import sys


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
    Get the path to the competitions.csv file.

    Returns:
        str: Full path to the competitions.csv file
    """
    return os.path.join(get_script_directory(), "competitions.csv")
