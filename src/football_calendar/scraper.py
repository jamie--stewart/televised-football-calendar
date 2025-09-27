"""Web scraping functionality for televised football fixtures."""

import logging

import requests
from user_agent import generate_user_agent

from .models import Fixture
from .parser import parse_fixtures_html

logger = logging.getLogger(__name__)

# HTTP headers for requests
headers = {
    "User-Agent": generate_user_agent(),
}


def get_fixtures_for_competition(competition_url: str) -> list[Fixture]:
    """
    Fetch fixtures for a given competition URL.

    Args:
        competition_url (str): URL to fetch fixtures from

    Returns:
        List[Fixture]: List of parsed fixtures from the competition
    """
    logger.info(f"Getting games for competition: {competition_url}")
    logger.debug(f"Making HTTP request to: {competition_url}")

    fixtures_page = requests.get(competition_url, headers=headers)
    logger.debug(f"HTTP response status: {fixtures_page.status_code}")
    logger.debug(f"HTTP response content length: {len(fixtures_page.content)} bytes")

    # Parse the HTML content and return fixtures
    return parse_fixtures_html(fixtures_page.content, competition_url)
