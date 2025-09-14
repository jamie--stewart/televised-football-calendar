import responses
from ics import Calendar

from televised_football_calendar import _output_path, generate_calendar_for_games, get_fixtures_for_competition


class TestChannelMapping:
    """Test TV channel name parsing and mapping."""

    @responses.activate
    def test_channel_mapping_accuracy(self, temp_output_dir, mixed_channels_html):
        """Test that various channel formats are correctly mapped."""
        responses.add(responses.GET, "http://test.com/mixed-channels", body=mixed_channels_html, status=200)

        fixtures = get_fixtures_for_competition("http://test.com/mixed-channels")
        calendar = generate_calendar_for_games(fixtures)

        output_path = _output_path("Mixed Channels", temp_output_dir)
        with open(output_path, "w") as f:
            f.writelines(calendar.serialize())

        with open(output_path) as f:
            generated_calendar = Calendar(f.read())

        events = list(generated_calendar.events)
        locations = {event.location for event in events}

        # Verify channel mappings
        expected_channels = {"Sky Sports", "BBC", "TNT Sports", "Amazon Prime"}
        assert expected_channels.issubset(locations)
