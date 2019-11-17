# TODO Convert to Beautiful Soup 4
#  Generate a football calendar
from lxml import html
from user_agent import generate_user_agent
from ics.icalendar import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import timedelta
import requests
import arrow
import argparse
import datetime
import sys
import os
import csv


program = argparse.ArgumentParser(description='Generate an .ics file of the televised Premier League fixtures')
program.add_argument('output_dir', help='The absolute path to the directory to place the .ics files in')
program.add_argument('--alert_minutes', type=int, help='The number of minutes before kick-off that you want an alert')

headers = {
    'User-Agent': generate_user_agent(),
}

SRC_DIR = os.path.dirname(sys.argv[0])


def _formatted_datetime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _output_path(competition_name, output_dir):
    formatted_competition_name = competition_name.lower().strip().replace('\'', '').replace(' ', '-')
    return os.path.join(output_dir, f'{formatted_competition_name}.ics')


def get_fixtures_for_competition(fixtures_url):

    print(f'Getting games for competition: {fixtures_url}')

    fixtures_page = requests.get(fixtures_url, headers=headers)
    html_tree = html.fromstring(fixtures_page.content)

    listings_rows = html_tree.xpath('//div[@id="listings"]/div[@class="container"]/div[@class="row-fluid"]')

    games = []

    match_date = None
    for row in listings_rows:

        date_elem = row.xpath('./div[contains(@class, "matchdate")]')
        if date_elem:  # Have a new match date
            if 'No Upcoming TV Fixtures' in date_elem[0].text:
                print(f'No games for competition {fixtures_url}')
                return games

            match_date = arrow.get(date_elem[0].text, 'dddd Do MMMM YYYY', tzinfo='Europe/London')

        else:  # This is a game
            fixture = ''
            try:
                home_team, away_team = [x.strip() for x in row.xpath('./div[contains(@class, "matchfixture")]')[0].text.split(' v ')]
                fixture = f'{home_team} vs {away_team}'
            except ValueError:
                if row.xpath('./div[contains(@class, "matchfixture")]')[0].text.strip() == 'TBC':
                    fixture = 'TBC'
                else:
                    raise ValueError('Could not parse format of \'matchfixture\' element')

            kickoff_time_text = row.xpath('./div[contains(@class, "kickofftime")]')[0].text

            if 'TBC' in kickoff_time_text:
                continue
            hour, minute = kickoff_time_text.split(':')

            kick_off = match_date.replace(hour=int(hour), minute=int(minute))

            # Seem to have &nbsp; characters in their text
            # ICS files are ascii-encoded
            competition = row.xpath('./div[contains(@class, "competition")]')[0].text.strip().encode('ascii', 'ignore')

            channel_text = row.xpath('./div[contains(@class, "channels")]')[0].text.lower()
            if 'sky' in channel_text:
                channel = 'Sky Sports'
            elif 'bbc' in channel_text:
                channel = 'BBC'
            elif 'bt sport' in channel_text:
                channel = 'BT Sport'
            elif 'itv' in channel_text:
                channel = 'ITV'
            elif 'tbc' in channel_text:
                channel = 'TBC'
            elif 'premier' in channel_text:
                channel = 'Premier Sports'
            elif 'eleven' in channel_text:
                channel = 'Eleven Sports'
            elif 'amazon prime video' in channel_text:
                channel = 'Amazon Prime'
            elif 's4c facebook' in channel_text:
                channel = 'S4C Facebook'
            elif 'rangers tv' in channel_text:
                channel = 'Rangers TV'
            elif 'celtic' in channel_text:
                channel = 'Celtic TV'
            else:
                raise ValueError(f'Television channel not recognised: {channel_text}')

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
        event.name = f'{game["fixture"]} ({game["competition"]})'
        start = game['kick_off']
        event.begin = start
        event.end = start.shift(hours=+2)
        event.location = game['channel']
        if args.alert_minutes:
            alarm = DisplayAlarm(trigger=timedelta(minutes=args.alert_minutes))
            event.alarms.append(alarm)
        calendar.events.add(event)

    return calendar


if __name__ == '__main__':

    args = program.parse_args()

    competitions_file = os.path.join(SRC_DIR, 'competitions.csv')
    with open(competitions_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            games = get_fixtures_for_competition(row['URL'])
            print(f'{_formatted_datetime()} Got {len(games)} games for {row["NAME"]}')

            output_path = _output_path(row['NAME'], args.output_dir)
            with open(output_path, 'w') as ics_file:

                print(f'{_formatted_datetime()} Writing games to {output_path}')
                ics_file.writelines(generate_calendar_for_games(games))
