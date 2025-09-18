import csv
import os
import sys
import tempfile
from pathlib import Path

import pytest
from freezegun import freeze_time

# Add parent directory to path so test modules can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
@freeze_time("2025-09-13 10:00:00")
def freeze_test_time():
    """Freeze time for all tests to make them deterministic."""
    pass


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_competitions_csv(temp_output_dir):
    """Create a temporary competitions.csv file for testing."""
    csv_path = os.path.join(temp_output_dir, "competitions.csv")
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["NAME", "URL"])
        writer.writerow(["Premier League", "http://test.com/premier-league"])
        writer.writerow(["FA Cup", "http://test.com/fa-cup"])
        writer.writerow(["Euro 2024", "http://test.com/euro-2024"])
    return csv_path


@pytest.fixture
def fixtures_dir():
    """Return the path to HTML fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def premier_league_normal_html():
    """Fixture containing normal Premier League HTML with fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "premier_league_normal.html"
    return fixture_path.read_text()


@pytest.fixture
def euro_2024_no_fixtures_html():
    """Fixture containing Euro 2024 HTML with no upcoming fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "euro_2024_no_fixtures.html"
    return fixture_path.read_text()


@pytest.fixture
def fa_cup_normal_html():
    """Fixture containing normal FA Cup HTML with fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "fa_cup_normal.html"
    return fixture_path.read_text()


@pytest.fixture
def mixed_channels_html():
    """Fixture containing HTML with mixed channel formats for testing channel mapping."""
    fixture_path = Path(__file__).parent / "fixtures" / "mixed_channels.html"
    return fixture_path.read_text()


@pytest.fixture
def mock_competitions_toml(temp_output_dir):
    """Create a temporary competitions.toml file for testing."""
    toml_content = """
[competitions]

[competitions.premier_league]
name = "Premier League"
url = "http://test.com/premier-league"
start_date = ""
team_filters = []

[competitions.fa_cup]
name = "FA Cup"
url = "http://test.com/fa-cup"
start_date = "2024-01-01"
team_filters = ["Arsenal", "Chelsea"]

[competitions.euro_2024]
name = "Euro 2024"
url = "http://test.com/euro-2024"
start_date = ""
team_filters = []
"""

    toml_path = os.path.join(temp_output_dir, "competitions.toml")
    with open(toml_path, "w") as f:
        f.write(toml_content)
    return toml_path
