"""Tests for TOML configuration functionality."""

import os
import tempfile
from datetime import datetime

import pytest

from models import Competition
from utils import load_competitions_config, should_include_fixture


@pytest.fixture
def temp_toml_config():
    """Create a temporary TOML config file for testing."""
    config_content = """
[competitions]

[competitions.premier_league]
name = "Premier League"
url = "http://test.com/premier-league"
start_date = "2024-01-15"
team_filters = ["Arsenal", "Chelsea.*", "Liverpool"]

[competitions.fa_cup]
name = "FA Cup"
url = "http://test.com/fa-cup"
start_date = ""
team_filters = []

[competitions.champions_league]
name = "Champions League"
url = "http://test.com/champions-league"
start_date = "2024-02-01"
team_filters = [".*City", "United.*"]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


def test_load_competitions_config(temp_toml_config, monkeypatch):
    """Test loading competitions from TOML config."""
    # Mock get_competitions_file_path to return our temp file
    monkeypatch.setattr("utils.get_competitions_file_path", lambda: temp_toml_config)

    config = load_competitions_config()

    assert len(config) == 3
    assert "premier_league" in config
    assert "fa_cup" in config
    assert "champions_league" in config

    # Test Premier League config
    pl_config = config["premier_league"]
    assert pl_config["name"] == "Premier League"
    assert pl_config["url"] == "http://test.com/premier-league"
    assert pl_config["start_date"] == "2024-01-15"
    assert pl_config["team_filters"] == ["Arsenal", "Chelsea.*", "Liverpool"]

    # Test FA Cup config (no filters)
    fa_config = config["fa_cup"]
    assert fa_config["name"] == "FA Cup"
    assert fa_config["url"] == "http://test.com/fa-cup"
    assert fa_config["start_date"] == ""
    assert fa_config["team_filters"] == []


def test_load_competitions_config_file_not_found(monkeypatch):
    """Test handling of missing TOML config file."""
    monkeypatch.setattr("utils.get_competitions_file_path", lambda: "/nonexistent/file.toml")

    config = load_competitions_config()

    assert config == {}


def test_should_include_fixture_date_filtering():
    """Test date filtering functionality."""
    # Test fixture after start date (should be included)
    kick_off = datetime(2024, 2, 1, 15, 0)
    config = {"start_date": "2024-01-15", "team_filters": []}

    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is True

    # Test fixture before start date (should be excluded)
    kick_off = datetime(2024, 1, 10, 15, 0)

    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is False

    # Test no start date (should be included)
    config = {"start_date": "", "team_filters": []}

    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is True


def test_should_include_fixture_team_filtering():
    """Test team name regex filtering functionality."""
    kick_off = datetime(2024, 2, 1, 15, 0)

    # Test exact team match
    config = {"start_date": "", "team_filters": ["Arsenal", "Chelsea"]}
    assert should_include_fixture("Arsenal vs Liverpool", kick_off, config) is True
    assert should_include_fixture("Chelsea vs Manchester United", kick_off, config) is True
    assert should_include_fixture("Liverpool vs Manchester United", kick_off, config) is False

    # Test regex patterns
    config = {"start_date": "", "team_filters": [".*City", "United.*"]}
    assert should_include_fixture("Manchester City vs Liverpool", kick_off, config) is True
    assert should_include_fixture("Leicester City vs Arsenal", kick_off, config) is True
    assert should_include_fixture("Manchester United vs Chelsea", kick_off, config) is True
    assert should_include_fixture("United Sheffield vs Arsenal", kick_off, config) is True
    assert should_include_fixture("Arsenal vs Liverpool", kick_off, config) is False

    # Test case insensitive matching
    config = {"start_date": "", "team_filters": ["arsenal"]}
    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is True
    assert should_include_fixture("ARSENAL vs Chelsea", kick_off, config) is True


def test_should_include_fixture_combined_filtering():
    """Test combined date and team filtering."""
    # Fixture that matches both date and team criteria
    kick_off = datetime(2024, 2, 1, 15, 0)
    config = {"start_date": "2024-01-15", "team_filters": ["Arsenal"]}

    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is True

    # Fixture that matches date but not team
    assert should_include_fixture("Liverpool vs Chelsea", kick_off, config) is False

    # Fixture that matches team but not date
    kick_off = datetime(2024, 1, 10, 15, 0)
    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is False


def test_should_include_fixture_tbc_fixtures():
    """Test handling of TBC (To Be Confirmed) fixtures."""
    kick_off = datetime(2024, 2, 1, 15, 0)
    config = {"start_date": "", "team_filters": ["Arsenal"]}

    # TBC fixtures should be included regardless of team filters
    assert should_include_fixture("TBC", kick_off, config) is True


def test_should_include_fixture_no_filters():
    """Test that fixtures are included when no filters are specified."""
    kick_off = datetime(2024, 2, 1, 15, 0)
    config = {"start_date": "", "team_filters": []}

    assert should_include_fixture("Any Team vs Another Team", kick_off, config) is True


def test_should_include_fixture_invalid_regex():
    """Test handling of invalid regex patterns."""
    kick_off = datetime(2024, 2, 1, 15, 0)
    config = {"start_date": "", "team_filters": ["[invalid regex"]}

    # Should return False when regex is invalid and no teams match
    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is False


def test_should_include_fixture_invalid_date_format():
    """Test handling of invalid date format in config."""
    kick_off = datetime(2024, 2, 1, 15, 0)
    config = {"start_date": "invalid-date", "team_filters": []}

    # Should include fixture when date format is invalid (falls back to no filtering)
    assert should_include_fixture("Arsenal vs Chelsea", kick_off, config) is True


def test_competition_model_with_filters():
    """Test Competition model with new filtering fields."""
    competition = Competition(
        name="Premier League",
        url="http://test.com/premier-league",
        start_date="2024-01-15",
        team_filters=["Arsenal", "Chelsea"],
    )

    assert competition.name == "Premier League"
    assert competition.url == "http://test.com/premier-league"
    assert competition.start_date == "2024-01-15"
    assert competition.team_filters == ["Arsenal", "Chelsea"]


def test_competition_model_defaults():
    """Test Competition model with default values."""
    competition = Competition(name="FA Cup", url="http://test.com/fa-cup")

    assert competition.name == "FA Cup"
    assert competition.url == "http://test.com/fa-cup"
    assert competition.start_date is None
    assert competition.team_filters == []
