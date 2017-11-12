from ics.icalendar import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import timedelta
import arrow


calendar = Calendar()

event = Event()
event.name = 'Test event'
start = arrow.get('Wednesday 21 January 2018 14:30', 'dddd D MMMM YYYY HH:mm')
event.begin = start
event.end = start.shift(hours=+2)

alarm = DisplayAlarm(trigger=timedelta(minutes=15))

event.alarms.add(alarm)
calendar.events.add(event)

print calendar

