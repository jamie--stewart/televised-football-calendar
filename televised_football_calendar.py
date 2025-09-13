#  Generate a football calendar
from bs4 import BeautifulSoup
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
program.add_argument('--alert-minutes', type=int, help='The number of minutes before kick-off that you want an alert')

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
    soup = BeautifulSoup(fixtures_page.content, 'html.parser')

    listings_rows = soup.find_all('div', class_=['fixture', 'fixture-date'])

    games = []

    match_date = None
    for row in listings_rows:
        if 'fixture-date' in row.get('class', []):  # Have a new match date
            if 'No Upcoming TV Fixtures' in row.text:
                print(f'No games for competition {fixtures_url}')
                return games

            match_date = arrow.get(row.text, 'dddd Do MMMM YYYY', tzinfo='Europe/London')

        else:  # This is a game
            fixture = ''
            
            teams_raw = row.find('div', class_='fixture__teams').get_text(strip=True)
            try:
                home_team, away_team = [team.strip() for team in teams_raw.split(' v ')]
                fixture = f'{home_team} vs {away_team}'
            except ValueError:
                if teams_raw.strip() == 'TBC':
                    fixture = 'TBC'
                else:
                    raise ValueError('Could not parse format of \'fixture__teams\' element')

        #     time_elem = row.xpath('./div[@class="fixture__time"]')
        # time_raw = time_elem[0].text

            kickoff_time_text = row.find('div', class_='fixture__time').get_text(strip=True)

            if 'TBC' in kickoff_time_text:
                continue
            hour, minute = kickoff_time_text.split(':')

            kick_off = match_date.replace(hour=int(hour), minute=int(minute))

            # Seem to have &nbsp; characters in their text
            # ICS files are ascii-encoded
            competition = row.find('div', class_='fixture__competition').get_text(strip=True).replace('\xa0', ' ').encode('ascii', 'ignore').decode('ascii')

            channels_elem = row.find('div', class_='fixture__channel')
            channels_text_raw = channels_elem.get_text(separator=' | ', strip=True).lower()
            if 'sky' in channels_text_raw:
                channel = 'Sky Sports'
            elif 'bbc' in channels_text_raw:
                channel = 'BBC'
            elif 'tnt sports' in channels_text_raw:
                channel = 'TNT Sports'
            elif 'itv' in channels_text_raw:
                channel = 'ITV'
            elif 'tbc' in channels_text_raw:
                channel = 'TBC'
            elif 'premier' in channels_text_raw:
                channel = 'Premier Sports'
            elif 'eleven' in channels_text_raw:
                channel = 'Eleven Sports'
            elif 'amazon prime video' in channels_text_raw:
                channel = 'Amazon Prime'
            elif 's4c facebook' in channels_text_raw:
                channel = 'S4C Facebook'
            elif 'rangers tv' in channels_text_raw:
                channel = 'Rangers TV'
            elif 'celtic' in channels_text_raw:
                channel = 'Celtic TV'
            else:
                raise ValueError(f'Television channel not recognised: {channels_text_raw}')

            game = {
                'fixture': fixture,
                'kick_off': kick_off,
                'channel': channel,
                'competition': competition
            }
            games.append(game)

    return games


def generate_calendar_for_games(games_array, alert_minutes=None):
    calendar = Calendar()

    for game in games_array:
        event = Event()
        event.name = f'{game["fixture"]} ({game["competition"]})'
        start = game['kick_off']
        event.begin = start
        event.end = start.shift(hours=+2)
        event.location = game['channel']
        if alert_minutes:
            alarm = DisplayAlarm(trigger=timedelta(minutes=alert_minutes))
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
            # TODOJ: Convert to a proper logger
            print(f'{_formatted_datetime()} Got {len(games)} games for {row["NAME"]}')

            output_path = _output_path(row['NAME'], args.output_dir)
            with open(output_path, 'w') as ics_file:

                print(f'{_formatted_datetime()} Writing games to {output_path}')
                calendar = generate_calendar_for_games(games, args.alert_minutes)
                ics_file.writelines(calendar.serialize())
