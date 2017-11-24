import requests
from lxml import html
from user_agent import generate_user_agent
from ics.icalendar import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import timedelta
import arrow
import argparse


program = argparse.ArgumentParser(description='Generate an .ics file of the televised Premier League fixtures')
program.add_argument('output_file', help='The absolute path to the output .ics file you wish to place the fixtures in')
program.add_argument('--alert_minutes', type=int, help='The number of minutes before kick-off that you want an alert')
args = program.parse_args()

headers = {
    'User-Agent': generate_user_agent(),
}

fixtures_page = requests.get('http://www.live-footballontv.com/live-premier-league-football-on-tv.html', headers=headers)
html_tree = html.fromstring(fixtures_page.content)

listings_rows = html_tree.xpath('//div[@id="listings"]/div[@class="container"]/div[@class="row-fluid"]')

games = []

match_date = None
for row in listings_rows:
    date_elem = row.xpath('./div[contains(@class, "matchdate")]')
    if date_elem: #Have a new match date
        match_date = arrow.get(date_elem[0].text, 'dddd Do MMMM YYYY')    
        # print 'Match date {}'.format(match_date.text)
    else: #This is a game
        home_team, away_team = [x.strip() for x in row.xpath('./div[contains(@class, "matchfixture")]')[0].text.split(' v ')]
        hour, minute = row.xpath('./div[contains(@class, "kickofftime")]')[0].text.split(':')
        kick_off = match_date.replace(hour=int(hour), minute=int(minute))
        channel = 'Sky Sports' if 'sky' in row.xpath('./div[contains(@class, "channels")]')[0].text.lower() else 'BT Sport'
        game = {
            'home_team': home_team,
            'away_team': away_team,
            'kick_off': kick_off,
            'channel': channel
        }
        games.append(game)       

calendar = Calendar()

for game in games:
    event = Event()
    event.name = '{} vs {}'.format(game['home_team'], game['away_team'])
    start = game['kick_off']
    event.begin = start
    event.end = start.shift(hours=+2)
    if args.alert_minutes:
        alarm = DisplayAlarm(trigger=timedelta(minutes=args.alert_minutes))
        event.alarms.add(alarm)
    calendar.events.add(event)

with open(args.output_file, 'w') as ics_file:
    ics_file.writelines(calendar)
