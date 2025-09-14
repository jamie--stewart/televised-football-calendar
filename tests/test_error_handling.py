import responses
from freezegun import freeze_time

from televised_football_calendar import get_fixtures_for_competition


class TestErrorHandling:
    """Test error handling and robustness when parsing malformed HTML."""

    @responses.activate
    @freeze_time("2024-01-15 12:00:00")
    def test_handles_missing_elements_gracefully(self):
        """Test that missing HTML elements don't crash the parser."""
        malformed_html = """
        <html>
            <body>
                <div class="fixture-date">Wednesday 17th January 2024</div>

                <!-- Fixture with missing teams element -->
                <div class="fixture">
                    <div class="fixture__time">19:45</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event | Sky Sports Premier League</div>
                </div>

                <!-- Fixture with missing time element -->
                <div class="fixture">
                    <div class="fixture__teams">Arsenal v Liverpool</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>

                <!-- Valid fixture for comparison -->
                <div class="fixture">
                    <div class="fixture__teams">Chelsea v Manchester City</div>
                    <div class="fixture__time">20:00</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>
            </body>
        </html>
        """

        url = "https://example.com/test"
        responses.add(responses.GET, url, body=malformed_html, status=200)

        # Should not crash and should return only the valid fixture
        games = get_fixtures_for_competition(url)

        assert len(games) == 1
        assert games[0]["fixture"] == "Chelsea vs Manchester City"
        assert games[0]["channel"] == "Sky Sports"

    @responses.activate
    @freeze_time("2024-01-15 12:00:00")
    def test_handles_invalid_date_format(self):
        """Test that invalid date formats don't crash the parser."""
        malformed_html = """
        <html>
            <body>
                <!-- Invalid date format -->
                <div class="fixture-date">Not A Valid Date</div>

                <div class="fixture">
                    <div class="fixture__teams">Arsenal v Liverpool</div>
                    <div class="fixture__time">19:45</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>

                <!-- Valid date follows -->
                <div class="fixture-date">Wednesday 17th January 2024</div>

                <div class="fixture">
                    <div class="fixture__teams">Chelsea v Manchester City</div>
                    <div class="fixture__time">20:00</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>
            </body>
        </html>
        """

        url = "https://example.com/test"
        responses.add(responses.GET, url, body=malformed_html, status=200)

        # Should not crash and should return only the fixture with valid date
        games = get_fixtures_for_competition(url)

        assert len(games) == 1
        assert games[0]["fixture"] == "Chelsea vs Manchester City"

    @responses.activate
    @freeze_time("2024-01-15 12:00:00")
    def test_handles_invalid_time_format(self):
        """Test that invalid time formats don't crash the parser."""
        malformed_html = """
        <html>
            <body>
                <div class="fixture-date">Wednesday 17th January 2024</div>

                <!-- Invalid time format -->
                <div class="fixture">
                    <div class="fixture__teams">Arsenal v Liverpool</div>
                    <div class="fixture__time">Not A Time</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>

                <!-- Time without colon -->
                <div class="fixture">
                    <div class="fixture__teams">Tottenham v Newcastle</div>
                    <div class="fixture__time">1945</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>

                <!-- Valid fixture -->
                <div class="fixture">
                    <div class="fixture__teams">Chelsea v Manchester City</div>
                    <div class="fixture__time">20:00</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>
            </body>
        </html>
        """

        url = "https://example.com/test"
        responses.add(responses.GET, url, body=malformed_html, status=200)

        # Should not crash and should return only the valid fixture
        games = get_fixtures_for_competition(url)

        assert len(games) == 1
        assert games[0]["fixture"] == "Chelsea vs Manchester City"

    @responses.activate
    @freeze_time("2024-01-15 12:00:00")
    def test_handles_unrecognized_channel_gracefully(self):
        """Test that unrecognized channels use 'Unknown' instead of crashing."""
        malformed_html = """
        <html>
            <body>
                <div class="fixture-date">Wednesday 17th January 2024</div>

                <div class="fixture">
                    <div class="fixture__teams">Arsenal v Liverpool</div>
                    <div class="fixture__time">19:45</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">New Unknown Channel</div>
                </div>
            </body>
        </html>
        """

        url = "https://example.com/test"
        responses.add(responses.GET, url, body=malformed_html, status=200)

        # Should not crash and should use 'Unknown' for channel
        games = get_fixtures_for_competition(url)

        assert len(games) == 1
        assert games[0]["fixture"] == "Arsenal vs Liverpool"
        assert games[0]["channel"] == "Unknown"

    @responses.activate
    @freeze_time("2024-01-15 12:00:00")
    def test_handles_invalid_team_format(self):
        """Test that invalid team formats don't crash the parser."""
        malformed_html = """
        <html>
            <body>
                <div class="fixture-date">Wednesday 17th January 2024</div>

                <!-- Team format without ' v ' -->
                <div class="fixture">
                    <div class="fixture__teams">Arsenal vs Liverpool</div>
                    <div class="fixture__time">19:45</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>

                <!-- Valid fixture -->
                <div class="fixture">
                    <div class="fixture__teams">Chelsea v Manchester City</div>
                    <div class="fixture__time">20:00</div>
                    <div class="fixture__competition">Premier League</div>
                    <div class="fixture__channel">Sky Sports Main Event</div>
                </div>
            </body>
        </html>
        """

        url = "https://example.com/test"
        responses.add(responses.GET, url, body=malformed_html, status=200)

        # Should not crash and should return only the valid fixture
        games = get_fixtures_for_competition(url)

        assert len(games) == 1
        assert games[0]["fixture"] == "Chelsea vs Manchester City"
