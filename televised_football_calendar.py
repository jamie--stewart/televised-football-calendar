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

competitions = [
    ("Premier League" , "http://www.live-footballontv.com/live-premier-league-football-on-tv.html"),
    ("FA Cup", "http://www.live-footballontv.com/live-fa-cup-football-on-tv.html"),
    ("Champions League" , "http://www.live-footballontv.com/live-champions-league-football-on-tv.html")
]

def get_fixtures_for_competition(competition_name, fixtures_page):
    fixtures_page = requests.get(fixtures_page, headers=headers)
    html_tree = html.fromstring(fixtures_page.content)     

    listings_rows = html_tree.xpath('//div[@id="listings"]/div[@class="container"]/div[@class="row-fluid"]')

    games = []

    match_date = None
    for row in listings_rows:
        date_elem = row.xpath('./div[contains(@class, "matchdate")]')
        if date_elem: #Have a new match date
            match_date = arrow.get(date_elem[0].text, 'dddd Do MMMM YYYY')    
        else: #This is a game
            home_team, away_team = [x.strip() for x in row.xpath('./div[contains(@class, "matchfixture")]')[0].text.split(' v ')]
            hour, minute = row.xpath('./div[contains(@class, "kickofftime")]')[0].text.split(':')
            kick_off = match_date.replace(hour=int(hour), minute=int(minute))
            channel_text = row.xpath('./div[contains(@class, "channels")]')[0].text.lower()
            if 'sky' in channel_text:
                channel = 'Sky Sports'
            elif 'bbc' in channel_text:
                channel = 'BBC'
            elif 'bt sport' in channel_text:
                channel = 'BT Sport'
            else:
                raise ValueError('Television channel not recognised: {}'.format(channel_text))
            game = {
                'home_team': home_team,
                'away_team': away_team,
                'kick_off': kick_off,
                'channel': channel,
                'competition': competition_name
            }
            games.append(game)  
    
    return games

def generate_calendar_for_games(games_array):
    calendar = Calendar()

    for game in games:
        event = Event()
        event.name = '{} vs {} ({})'.format(game['home_team'], game['away_team'], game['competition'])
        start = game['kick_off']
        event.begin = start
        event.end = start.shift(hours=+2)
        event.location = game['channel']
        if args.alert_minutes:
            alarm = DisplayAlarm(trigger=timedelta(minutes=args.alert_minutes))
            event.alarms.add(alarm)
        calendar.events.add(event)
    
    return calendar

games = []
for competition_name, competition_url in competitions:
    games.extend(get_fixtures_for_competition(competition_name, competition_url))


with open(args.output_file, 'w') as ics_file:
    ics_file.writelines(generate_calendar_for_games(games))
