# Premier League Calendar

> Simple script to generate a .ics file of the (UK) televised Premier League fixtures

## Usage

* Install requirements:

`pip install -r requirements.txt`

* Use:

`python premier_league_tv_calendar.py <output_dir> [--alert_minutes <mins>]`

Where:

* `<output_dir>` is the *absolute* path to the directory you want to place each competition's .ics file
* `--alert_minutes <mins>` (optional) is the number of minutes before kick-off that you would like an alert of the game
