# Premier League Calendar

> Simple script to generate a .ics file of the (UK) televised Premier League fixtures

## Usage

* Install requirements:

`pip install -r requirements.txt`

* Use:

`python premier_league_tv_calendar.py <output_ics> [--alert_minutes <mins>]`

Where:

* `<output_ics>` is the *absolute* path to the .ics file you want to generate
* `--alert_minutes <mins>` (optional) is the number of minutes before kick-off that you would like an alert of the game

## Misc.

[Installing PIP module from Git](https://pip.pypa.io/en/stable/reference/pip_install/#git)