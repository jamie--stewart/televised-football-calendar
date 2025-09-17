import responses
from ics import Calendar

from generator import generate_calendar
from scraper import get_fixtures_for_competition
from utils import get_output_path


class TestDateTimeHandling:
    """Test date and time parsing functionality."""

    @responses.activate
    def test_datetime_parsing_accuracy(self, temp_output_dir, premier_league_normal_html):
        """Test that fixture dates and times are correctly parsed."""
        responses.add(responses.GET, "http://test.com/premier-league", body=premier_league_normal_html, status=200)

        fixtures = get_fixtures_for_competition("http://test.com/premier-league")
        calendar = generate_calendar(fixtures)

        output_path = get_output_path("Premier League", temp_output_dir)
        with open(output_path, "w") as f:
            f.writelines(calendar.serialize())

        with open(output_path) as f:
            generated_calendar = Calendar(f.read())

        events = list(generated_calendar.events)

        # Find the Arsenal vs Manchester City match (17:30 on Saturday 14th)
        arsenal_match = next(e for e in events if "Arsenal vs Manchester City" in e.name)

        # Verify date and time (converted from 17:30 BST to 16:30 UTC)
        assert arsenal_match.begin.day == 14  # 14th September
        assert arsenal_match.begin.month == 9  # September
        assert arsenal_match.begin.year == 2025
        assert arsenal_match.begin.hour == 16  # 17:30 BST = 16:30 UTC
        assert arsenal_match.begin.minute == 30

        # Verify timezone (should be UTC in ICS output)
        assert str(arsenal_match.begin.tzinfo) in ["UTC", "+00:00", "utc", "tzutc()"]
