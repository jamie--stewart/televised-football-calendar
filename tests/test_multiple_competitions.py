import os

import responses
from ics import Calendar

from src.football_calendar.generator import generate_calendar
from src.football_calendar.scraper import get_fixtures_for_competition
from src.football_calendar.utils import get_output_path


class TestMultipleCompetitions:
    """Test handling of multiple competitions and separate file generation."""

    @responses.activate
    def test_generates_separate_files_for_each_competition(
        self, temp_output_dir, premier_league_normal_html, fa_cup_normal_html
    ):
        """Test that separate ICS files are created for each competition."""
        # Setup mock responses for multiple competitions
        responses.add(responses.GET, "http://test.com/premier-league", body=premier_league_normal_html, status=200)
        responses.add(responses.GET, "http://test.com/fa-cup", body=fa_cup_normal_html, status=200)

        # Process Premier League
        pl_fixtures = get_fixtures_for_competition("http://test.com/premier-league")
        pl_calendar = generate_calendar(pl_fixtures)
        pl_output = get_output_path("Premier League", temp_output_dir)
        with open(pl_output, "w") as f:
            f.writelines(pl_calendar.serialize())

        # Process FA Cup
        fa_fixtures = get_fixtures_for_competition("http://test.com/fa-cup")
        fa_calendar = generate_calendar(fa_fixtures)
        fa_output = get_output_path("FA Cup", temp_output_dir)
        with open(fa_output, "w") as f:
            f.writelines(fa_calendar.serialize())

        # Verify both files exist
        assert os.path.exists(pl_output)
        assert os.path.exists(fa_output)
        assert pl_output.endswith("premier-league.ics")
        assert fa_output.endswith("fa-cup.ics")

        # Verify content separation
        with open(pl_output) as f:
            pl_cal = Calendar(f.read())
        with open(fa_output) as f:
            fa_cal = Calendar(f.read())

        pl_events = list(pl_cal.events)
        fa_events = list(fa_cal.events)

        assert len(pl_events) == 3  # Premier League fixtures
        assert len(fa_events) == 2  # FA Cup fixtures

        # Verify competition names in events
        for event in pl_events:
            assert "Premier League" in event.name
        for event in fa_events:
            assert "FA Cup" in event.name
