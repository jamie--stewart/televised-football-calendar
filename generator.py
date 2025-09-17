"""Calendar generation functionality for televised football fixtures."""

from datetime import timedelta
from typing import Optional

from ics.alarm import DisplayAlarm
from ics.icalendar import Calendar, Event

from models import Fixture


def generate_calendar(fixtures: list[Fixture], alert_minutes: Optional[int] = None) -> Calendar:
    """
    Generate an ICS calendar from a list of fixtures.

    Args:
        fixtures (List[Fixture]): List of fixtures to add to the calendar
        alert_minutes (Optional[int]): Minutes before kick-off to set alerts

    Returns:
        Calendar: ICS calendar object with all fixtures as events
    """
    calendar = Calendar()

    for fixture in fixtures:
        event = Event()
        event.name = f"{fixture.fixture} ({fixture.competition})"
        start = fixture.kick_off
        event.begin = start
        event.end = start.shift(hours=+2)  # Assume 2-hour duration
        event.location = fixture.channel

        if alert_minutes:
            alarm = DisplayAlarm(trigger=timedelta(minutes=alert_minutes))
            event.alarms.append(alarm)

        calendar.events.add(event)

    return calendar
