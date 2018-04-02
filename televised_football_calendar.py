import requests
from lxml import html
from user_agent import generate_user_agent
from ics.icalendar import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import timedelta
import arrow
import argparse
import datetime
import sys
import os
import csv
import unicodedata


program = argparse.ArgumentParser(description='Generate an .ics file of the televised Premier League fixtures')
program.add_argument('output_file', help='The absolute path to the output .ics file you wish to place the fixtures in')
program.add_argument('--alert_minutes', type=int, help='The number of minutes before kick-off that you want an alert')

headers = {
    'User-Agent': generate_user_agent(),
}

SRC_DIR = os.path.dirname(sys.argv[0])
log_file = os.path.join(SRC_DIR, 'output.log')
sys.stdout = open(log_file, 'a')

def formatted_datetime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_fixtures_for_competition(fixtures_url):
    fixtures_page = requests.get(fixtures_url, headers=headers)
    html_tree = html.fromstring(fixtures_page.content)     

    listings_rows = html_tree.xpath('//div[@id="listings"]/div[@class="container"]/div[@class="row-fluid"]')

    games = []

    match_date = None
    for row in listings_rows:

        date_elem = row.xpath('./div[contains(@class, "matchdate")]')
        if date_elem: #Have a new match date
            if 'No Upcoming TV Fixtures' in date_elem[0].text:
                print 'No games for competition {}'.format(fixtures_url)
                return games

            match_date = arrow.get(date_elem[0].text, 'dddd Do MMMM YYYY', tzinfo='Europe/London')    

        else: #This is a game
            fixture = ''
            try:
                home_team, away_team = [x.strip() for x in row.xpath('./div[contains(@class, "matchfixture")]')[0].text.split(' v ')]
                fixture = '{} vs {}'.format(home_team, away_team)
            except ValueError:
                if row.xpath('./div[contains(@class, "matchfixture")]')[0].text.strip() == 'TBC':
                    fixture = 'TBC'
                else:
                    raise ValueError('Could not parse format of \'matchfixture\' element')

            hour, minute = row.xpath('./div[contains(@class, "kickofftime")]')[0].text.split(':')
            
            kick_off = match_date.replace(hour=int(hour), minute=int(minute))

            #Seem to have &nbsp; characters in their text
            competition = row.xpath('./div[contains(@class, "competition")]')[0].text.strip().encode('ascii', 'ignore')
            
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
                'fixture': fixture,
                'kick_off': kick_off,
                'channel': channel,
                'competition': competition
            }
            games.append(game)  

    return games

def generate_calendar_for_games(games_array):
    calendar = Calendar()

    for game in games:
        event = Event()
        event.name = '{} ({})'.format(game['fixture'], game['competition'])
        start = game['kick_off']
        event.begin = start
        event.end = start.shift(hours=+2)
        event.location = game['channel']
        if args.alert_minutes:
            alarm = DisplayAlarm(trigger=timedelta(minutes=args.alert_minutes))
            event.alarms.add(alarm)
        calendar.events.add(event)
    
    return calendar

if __name__ == '__main__':
    
    args = program.parse_args()
    games = []

    competitions_file = os.path.join(SRC_DIR, 'competitions.csv')
    with open (competitions_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            current_length = len(games)
            games.extend(get_fixtures_for_competition(row['URL']))
            print '{} Got {} games for {}'.format(formatted_datetime(), len(games) - current_length, row['NAME'])

    with open(args.output_file, 'w') as ics_file:
        print '{} Writing games to {}'.format(formatted_datetime(), os.path.abspath(args.output_file))
        ics_file.writelines(generate_calendar_for_games(games))
