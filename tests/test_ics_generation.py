import os
from datetime import timedelta

import pytest
import responses
from ics import Calendar

from src.football_calendar.generator import generate_calendar
from src.football_calendar.models import Fixture
from src.football_calendar.scraper import get_fixtures_for_competition
from src.football_calendar.utils import get_output_path


class TestBasicICSGeneration:
    """Test basic ICS file generation functionality."""

    @responses.activate
    def test_generates_valid_ics_file_with_correct_events(self, temp_output_dir, premier_league_normal_html):
        """Test that a valid ICS file is generated with correct event structure."""
        # Setup mock response
        responses.add(responses.GET, "http://test.com/premier-league", body=premier_league_normal_html, status=200)

        # Get fixtures and generate calendar
        fixtures = get_fixtures_for_competition("http://test.com/premier-league")
        calendar = generate_calendar(fixtures)

        # Write to file
        output_path = get_output_path("Premier League", temp_output_dir)
        with open(output_path, "w") as f:
            f.writelines(calendar.serialize())

        # Verify file exists and is readable
        assert os.path.exists(output_path)
        assert output_path.endswith("premier-league.ics")

        # Parse the generated ICS file
        with open(output_path) as f:
            generated_calendar = Calendar(f.read())

        # Verify calendar structure
        events = list(generated_calendar.events)
        assert len(events) == 3  # Should have 3 fixtures from our test data

        # Verify first event details
        arsenal_city = next(e for e in events if "Arsenal vs Manchester City" in e.name)
        assert "Arsenal vs Manchester City" in arsenal_city.name
        assert "Premier League" in arsenal_city.name
        assert arsenal_city.location == "Sky Sports"
        assert arsenal_city.begin.hour == 16  # 17:30 BST = 16:30 UTC
        assert arsenal_city.begin.minute == 30
        # Verify 2-hour duration
        duration = arsenal_city.end - arsenal_city.begin
        assert duration.total_seconds() == 2 * 60 * 60  # 2 hours

    @responses.activate
    def test_handles_no_upcoming_fixtures(self, temp_output_dir, euro_2024_no_fixtures_html):
        """Test handling of 'No Upcoming TV Fixtures' message."""
        responses.add(responses.GET, "http://test.com/euro-2024", body=euro_2024_no_fixtures_html, status=200)

        fixtures = get_fixtures_for_competition("http://test.com/euro-2024")
        calendar = generate_calendar(fixtures)

        output_path = get_output_path("Euro 2024", temp_output_dir)
        with open(output_path, "w") as f:
            f.writelines(calendar.serialize())

        # Verify empty calendar
        with open(output_path) as f:
            generated_calendar = Calendar(f.read())

        events = list(generated_calendar.events)
        assert len(events) == 0

    @responses.activate
    def test_generates_calendar_with_alarms(self, premier_league_normal_html):
        """Test that alarms are correctly set when alert_minutes is provided."""
        responses.add(responses.GET, "http://test.com/premier-league", body=premier_league_normal_html, status=200)

        fixtures = get_fixtures_for_competition("http://test.com/premier-league")
        calendar = generate_calendar(fixtures, alert_minutes=30)

        events = list(calendar.events)
        assert len(events) == 3

        # Check that all events have alarms
        for event in events:
            assert len(event.alarms) == 1
            alarm = list(event.alarms)[0]
            # Alarm should trigger 30 minutes BEFORE the event
            assert alarm.trigger == timedelta(minutes=-30)

    @responses.activate
    def test_generates_calendar_without_alarms_when_none_specified(self, premier_league_normal_html):
        """Test that no alarms are set when alert_minutes is None."""
        responses.add(responses.GET, "http://test.com/premier-league", body=premier_league_normal_html, status=200)

        fixtures = get_fixtures_for_competition("http://test.com/premier-league")
        calendar = generate_calendar(fixtures, alert_minutes=None)

        events = list(calendar.events)
        for event in events:
            assert len(event.alarms) == 0

    @pytest.mark.parametrize(
        "alert_minutes,expected_trigger",
        [
            (15, timedelta(minutes=-15)),  # 15 min before
            (60, timedelta(minutes=-60)),  # 1 hour before
            (1440, timedelta(minutes=-1440)),  # 1 day before
        ],
    )
    def test_alarm_timing_scenarios(self, alert_minutes, expected_trigger):
        """Test various alarm timing scenarios."""
        import arrow

        fixture = Fixture(
            fixture="Arsenal vs Chelsea",
            kick_off=arrow.Arrow(2024, 1, 1, 15, 0),  # 3 PM
            competition="Premier League",
            channel="Sky Sports",
        )

        calendar = generate_calendar([fixture], alert_minutes=alert_minutes)
        event = list(calendar.events)[0]
        alarm = list(event.alarms)[0]
        assert alarm.trigger == expected_trigger

    def test_ics_file_contains_correct_alarm_syntax(self, temp_output_dir):
        """Test that generated ICS file has proper VALARM syntax."""
        import arrow

        fixture = Fixture(
            fixture="Arsenal vs Chelsea",
            kick_off=arrow.Arrow(2024, 1, 1, 15, 0),
            competition="Premier League",
            channel="Sky Sports",
        )
        calendar = generate_calendar([fixture], alert_minutes=30)

        # Write and read back the ICS file
        output_path = get_output_path("Test", temp_output_dir)
        with open(output_path, "w") as f:
            f.writelines(calendar.serialize())

        with open(output_path) as f:
            ics_content = f.read()

        # Verify VALARM block exists with correct trigger
        assert "BEGIN:VALARM" in ics_content
        assert "TRIGGER:-PT30M" in ics_content  # -30 minutes in RFC format
        assert "ACTION:DISPLAY" in ics_content
        assert "END:VALARM" in ics_content
