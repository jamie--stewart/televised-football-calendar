import pytest
import responses
import os
from ics import Calendar
from televised_football_calendar import get_fixtures_for_competition, generate_calendar_for_games, _output_path


class TestBasicICSGeneration:
    """Test basic ICS file generation functionality."""
    
    @responses.activate
    def test_generates_valid_ics_file_with_correct_events(self, temp_output_dir, premier_league_normal_html):
        """Test that a valid ICS file is generated with correct event structure."""
        # Setup mock response
        responses.add(
            responses.GET,
            "http://test.com/premier-league",
            body=premier_league_normal_html,
            status=200
        )
        
        # Get fixtures and generate calendar
        fixtures = get_fixtures_for_competition("http://test.com/premier-league")
        calendar = generate_calendar_for_games(fixtures)
        
        # Write to file
        output_path = _output_path("Premier League", temp_output_dir)
        with open(output_path, 'w') as f:
            f.writelines(calendar.serialize())
        
        # Verify file exists and is readable
        assert os.path.exists(output_path)
        assert output_path.endswith("premier-league.ics")
        
        # Parse the generated ICS file
        with open(output_path, 'r') as f:
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
        responses.add(
            responses.GET,
            "http://test.com/euro-2024",
            body=euro_2024_no_fixtures_html,
            status=200
        )
        
        fixtures = get_fixtures_for_competition("http://test.com/euro-2024")
        calendar = generate_calendar_for_games(fixtures)
        
        output_path = _output_path("Euro 2024", temp_output_dir)
        with open(output_path, 'w') as f:
            f.writelines(calendar.serialize())
        
        # Verify empty calendar
        with open(output_path, 'r') as f:
            generated_calendar = Calendar(f.read())
        
        events = list(generated_calendar.events)
        assert len(events) == 0